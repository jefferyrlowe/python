#!/usr/bin/env python

import os
import sys
import time
import errno
import ctypes
import exceptions
import subprocess

__doc__ = '''
measure a SPARC CPU's clock rate

Usage: clockrate.py [options]

Options:
  -h, --help      show this help message and exit
  --chip          use the first active CPU found for each chip (default)
  --core          use the first active CPU found for each core
  --allcpus       report clock rate for all active CPUs
  --cpu=CPUS      report clock rate for specified CPUs, regardless of state
  -i INTERVAL     clock rate sample interval in seconds (default=1.0)
  -c SAMPLECOUNT  number of samples to collect (default=-1)
  -t THRESHOLD    report clock rates below threshold  (default=100)

This script will cycle through the CPUs indicated and measure the clock
rate in MHz for each CPU. For --chip and --core, a representative CPU
is chosen by locating the first CPU within the chip or core grouping
this either on-line or in the no-intr state.  If --allcpus is
specified, all CPUs whose state is on-line or no-intr will be
reported. 

Individual CPUs can be specified by identifier using the '--cpu=CPUS'
option.  CPUS can be specified using the following methods:

 CPU Id List:
       --cpu=0,1,4,10,24,4

 CPU Id Range:  
       --cpu=12-30

 All CPUs:
       --cpu=all

 Note: ranges and lists of CPU identifiers can be mixed together, e.g.:

       --cpu=0-5,10,11,30-35,7

       This is equivalent to:

       --cpu=0,1,2,3,4,5,7,10,11,30,31,32,33,34,35

The default options when nothing is specified on the command line are:

 clockrate.py --chip -i 1.0 -c -1 -t 100


Warning: Given the single threaded nature of interpreted languages,
         python specifically, this script will induce a load on the
         host which may be undesirable for long-term observation.


HISTORY

21 Aug 2018 - Version 1.7
- added support related to CPU pools

21 Jun 2013 - Version 1.6
- fixed bug in sample_loop
  reference sampleInterval value before assignment

20 Jun 2013 - Version 1.5
- changed --cpu command line option parsing to allow embedded ranges
- added --version command line switch
- added cpu id list de-duplicating and sorting to CPU.query function,
- added optional argument to CPU.query: strictChecking
- added MissingCPU exception, thrown by CPU.query when strictChecking
        is True and the number of requested cpuids is greater than the
        number of found CPUs.

19 Jun 2013 - Version 1.4
- fixed command line specification of list of CPUs to monitor
- changed --cpu to --cpu=CPUS,
  CPUS is a comma-delimited list of CPU ids or the string "all"
- added --allcpu option, equivalent to --cpu=all
- added parse_cmdline function 
  function uses deprecated optparse module

18 Jun 2013 - Version 1.3
- fixed state filtering in CPU chip & core class methods
- changed command-line options and handling (again)

22 Apr 2013 - Version 1.2
- added chip/core filter to command-line processing
- added chip/core class methods to CPU class
- added state filtering to CPU.query classmethod
- added sample_loop function
- added timestamp function
- added chip and core identifiers to output
- added poweradm detection
- removed sampling loop from __main__
- changed command-line options and handling

19 Apr 2013 - Version 1.1
- added CError exception, subclass of OSError
- added LIBC class
- added CPU class, child class of LIBC
- changed SPARCRegister now a child class of LIBC
- changed all exceptions raised from calling libc functions to CError
- removed _libc global data
- removed reported_clockrates function
- removed bind function
- removed measure_clockrate function

18 Apr 2013 - Version 1.0
- initial release
'''

Author = "erik.oshaughnessy@oracle.com modified by rick.weisner@oracle.com"
Version = "1.7"

##
## Constants lifted from various C header files, makes calling the
## C foreign functions a little more friendly.
##
P_PID               = 0                  # sys/procset.h
P_MYID              = -1                 # sys/procset.h
PS_NONE             = -1                 # sys/pset.h
PS_QUERY            = -2                 # sys/pset.h
PBIND_NONE          = -1                 # sys/processor.h
PBIND_QUERY         = -2                 # sys/processor.h
PROT_RWX            = 0x1 | 0x2 | 0x4    # sys/mman.h
SC_NPROCESSORS_ONLN = ctypes.c_int32(15) # unistd.h
global USE_PSET_BIND        #rcw

##
## Classes
##


class CError(exceptions.OSError):
    '''
    Raised when foreign functions called via ctypes return errors.
    Will retrieve errno from ctypes via ctypes.get_errno() and then
    determine the proper errno string via os.strerror(). The optional
    msg argument can be any string or value the user supplies.
    '''
    def __init__(self, msg=None):
        '''
        '''
        err = ctypes.get_errno()
        super(CError, self).__init__(err, os.strerror(err), msg)

class MissingCPU(Exception):
    '''
    Raised when the found set of CPUs does not match the requested
    set of CPU identifiers.
    '''
    def __init__(self,missingIDs,foundIDs=None):
        self.missingIDs = ','.join([str(x) for x in missingIDs])
        self.foundIDs = ','.join([str(x) for x in foundIDs])

    def __str__(self):
        return "CPUs were not found: %s" % self.missingIDs

class LIBC(object):
    '''
    Provides a foundation object to minimize the number of duplicated
    libc handles.
    '''
    _libc = ctypes.CDLL('libc.so', use_errno=True)
    _libc.gethrtime.restype = ctypes.c_uint64 # uint64_t gethrtime(void)
    _libc.valloc.restype = ctypes.c_void_p    # void *valloc(size_t)


class SPARCRegister(LIBC):
    '''
    Provides Pythonic access to a SPARC CPU register. The class is
    initialized with a ctypes.c_uint32() array of valid SPARC machine
    instructions that comprise a function whose call signature in C
    would look like:

    void func(uint64_t *)

    The instructions for the function are copied into a page-aligned
    buffer which has had it's page permissions modified to
    read/write/execute using mprotect(2) from libc.

    Finally,  a python-callable foreign function is constructed from a
    pointer to the page-aligned buffer. 

    The user-provided instructions are expected to perform whatever
    actions necessary to retrieve the desired SPARC register contents
    and store the contents at the address provided in the function
    argument.  Instructions must be position-independent.

    Yes,  it's magic.
    '''
    def __init__(self, getterInstructions):
        '''
        getterInstructions is an array of ctypes.c_uint32's initialized
        with SPARC machine instructions.

        e.g.

        G0_ASM = (ctypes.c_uint32 * 4)(0x81c3e008,  # retl
                                       0xc0720000,  #   stx %g0,  [%o0]
                                       0x00000000,  # illtrap 0
                                       0x00000000) # illtrap 0
        GlobalZero = SPARCRegister(G0_ASM)

        if GlobalZero.value != 0:
            raise Exception("%g0 != 0")
        '''
        bufsiz = ctypes.sizeof(getterInstructions)
        self._ibuf = self._libc.valloc(bufsiz)
        if self._ibuf is None:
            raise CError("valloc")

        if self._libc.mprotect(self._ibuf, bufsiz, PROT_RWX) != 0:
            raise CError("mprotect")

        ctypes.memmove(self._ibuf, getterInstructions, bufsiz)
        prototype = ctypes.CFUNCTYPE(None, ctypes.POINTER(ctypes.c_uint64))
        fptr = ctypes.cast(self._ibuf, prototype)
        self._getter = prototype(fptr)

    def __del__(self):
        '''
        Free the memory allocated via libc's valloc(3C).
        '''
        self._libc.free(self._ibuf)

    @property
    def value(self):
        '''
        Executes a foreign function call to fetch a register value.
        '''
        v = ctypes.c_uint64()
        self._getter(ctypes.byref(v))
        return v.value


class Tick(SPARCRegister):
    '''
    %tick is a SPARCv9 per-CPU 63-bit register that counts CPU clock
    cycles.  Values obtained from the %tick register on one CPU cannot
    be compared against values obtained from another CPU's %tick
    register.

    This class provides access to the %tick register via the 'value'
    property.  When the value property is accessed,  %tick is fetched
    for the CPU that the python instance is currently executing on.
    It is highly recommended that callers bind the python process to a
    target CPU before attempting to make repeated samples of the %tick
    register.

    e.g.

    tick = Tick()
    if ctypes.CDLL("libc.so").processor_bind(0, -1, TARGETCPU, None) == 0:
        while True:
            print tick.value
    '''

    ## The following array,  _ASM,  contains SPARC machine instructions
    ## which implement a leaf-function that will read the %tick register
    ## of the CPU the process is executing on and then writes the 64-bit
    ## value obtained to the address supplied by the caller.  The illtrap
    ## provides insurance that the function returns to the caller,  otherwise
    ## the process will abend when the illtrap instruction is executed with
    ## a message similar to:
    ##
    ## Illegal instruction (core dumped)
    ## 
    _ASM = (ctypes.c_uint32 * 4)(0x93410000,  # rd %tick,  %o1
                                 0x81c3e008,  # retl
                                 0xd2720000,  #   stx %o1,  [%o0]
                                 0)           # illtrap 0

    def __init__(self):
        super(Tick, self).__init__(self._ASM)

    @property
    def value(self):
        '''
        Returns the %tick register contents for the CPU that the
        calling process is executing on currently.
        '''
        ##
        ## I didn't need to over-ride the value method here,  but 
        ##
        return super(Tick, self).value


class CPU(LIBC):
    '''
    Provides access to per-CPU data.
    '''
    _tick = Tick()

    @classmethod
    def query(cls, cpuids=None, states=None,strictChecking=False):
        '''
        Returns a list of CPU objects initialized from the
        output of '/usr/bin/kstat -p cpu_info'.  The cpuids
        argument can be used to filter the list of CPUs returned
        ( if it is not None and is a list of integer CPU ids ).
        '''

        if cpuids and len(cpuids) == 0:
            cpuids = None

        if cpuids is not None:
            cpuids = sorted(set(cpuids)) # de-dup, sort cpuids list
#rcw
        mypid = os.getpid()
#rcw   Am I running in a pset ? 
        IN_PSET = 0  # not in pset may need to pst_bins
        p2 = subprocess.Popen(['/usr/sbin/psrset', '-q', str(mypid)], 
                             stdout=subprocess.PIPE)
        for line2 in p2.stdout:
            (myprocessor,dummy,pset_id_dummy) = line2.strip().partition(' ')
            mypset=pset_id_dummy.split();
            pset_id = mypset[2]
            if pset_id == 'not':
              	IN_PSET = 0 # pset binding 
            else:
                IN_PSET = 1 #  in pset, no pset_bind

	global USE_PSET_BIND
        if IN_PSET == 1:
            USE_PSET_BIND=0
#rcw
        if IN_PSET == 0:
          p0 = subprocess.Popen(['/usr/bin/svcs', 'svc:/system/pools:default'], 
                               stdout=subprocess.PIPE)
          USE_PSET_BIND = 1  # use pset_bind and all CPUS
          for line0 in p0.stdout:
              (mystatus, sep, val) = line0.strip().partition(' ')
              if mystatus == 'online':
              	  USE_PSET_BIND = 0 # no pset binding only cpus in global
#rcw
        pcpus = {}
        if USE_PSET_BIND == 0:
          p1 = subprocess.Popen(['/usr/sbin/psrset', '-p'], 
                             stdout=subprocess.PIPE)
          for line1 in p1.stdout:
            (keys, sep, val) = line1.strip().partition('\t')
            (processor, instances, pset) = keys.split(' ')
            (instance,dummy) = instances.split(':')
            if IN_PSET == 0:
              pcpus[int(instance)] = int(instance)
            else:
              if pset == pset_id:
                pcpus[int(instance)] = int(instance)

#rcw
        p = subprocess.Popen(['/usr/bin/kstat', '-p', 'cpu_info'], 
                             stdout=subprocess.PIPE)
        cpus = {}

        for line in p.stdout:
            (keys, sep, val) = line.strip().partition('\t')
            (module, instance, name, key) = keys.split(':')
            if ( USE_PSET_BIND == 0 and IN_PSET == 0 and int(instance) not in pcpus ) or ( IN_PSET == 1 and int(instance) in pcpus) or (USE_PSET_BIND == 1 ):
              try:
                   if int(instance) not in cpuids:
                       continue
              except TypeError:
                   pass            # cpuids is None, find all CPUs

              cpu = cpus.setdefault(instance, CPU(instance))
  
              # First try to treat val as an integer 
              # Next treat val as float
              # Finally,  treat val as string
              try:
                 setattr(cpu, key, int(val))
              except ValueError:
                try:
                    setattr(cpu, key, float(val))
                except ValueError:
                    setattr(cpu, key, val)

              cpus[instance] = cpu

        if states:
               for cpu in cpus.values():
                   if cpu.state in states:
                       continue
                   cpus[cpu.cpuid] = None
                   del(cpu)

        if cpuids and strictChecking and len(cpus) != len(cpuids):
               askedfor = set(cpuids)
               found = set([x.cpuid for x in cpus.values()])
               common = askedfor.intersection(found)
               notfound = askedfor.difference(common)
               if len(notfound):
                   raise MissingCPU(notfound,common)

        return sorted(cpus.values())

    @classmethod
    def chips(cls, cpus=None,  states=None):
        '''
        Sorts CPUs into buckets organized by chip_id. Returns a dictionary
        of CPU arrays structured thusly:

        { chip_id: [CPU(), ...],  ... }
        '''
        chips = {}

        if cpus is None:
            cpus = cls.query(states=states)

        else:
            if states:
                for cpu in cpus.values():
                    if cpu.state in states:
                        continue
                    cpus[cpu.cpuid] = None
                    del(cpu)

        for cpu in cpus:
            l = chips.setdefault(cpu.chip_id, [])
            l.append(cpu)
            chips[cpu.chip_id] = l

        return chips

    @classmethod
    def cores(cls, cpus=None, states=None):
        '''
        Sorts CPUs into buckets organized by core_id.  Returns a dictionary
        of CPU arrays structured thusly:

        { core_id: [CPU(), ...],  ... }
        '''
        cores = {}

        if cpus is None:
            cpus = cls.query(states=states)
        else:
            if states:
                for cpu in cpus.values():
                    if cpu.state in states:
                        continue
                    cpus[cpu.cpuid] = None
                    del(cpu)

        for cpu in cpus:
            l = cores.setdefault(cpu.core_id, [])
            l.append(cpu)
            cores[cpu.core_id] = l
        return cores

    def __init__(self, cpuid):
        self.cpuid = int(cpuid)
        self._psetid = PS_NONE
        self.cpuid = int(cpuid)

    def __repr__(self):
        return 'CPU(id=%s,chip=%s,core=%s' % (self.cpuid,self.chip_id,self.core_id)

    def __str__(self):
        '''
        CPU pretty printing
        '''
        s = []
        s.append('CPU: %s' % (self.cpuid))
        attrnames = self.__dict__.keys()
        attrnames.remove('cpuid')
        for k in sorted(attrnames):
            s.append('\t%s = %s' % (k, self.__dict__[k]))
        return '\n'.join(s)

    def __cmp__(self, other):
        '''
        Compares CPUs by their cpuid attribute.  This has the side-effect
        of ordering CPUs by chip and core identifiers as well.
        '''
        return cmp(self.cpuid, other.cpuid)

    @property
    def psetid(self):
        '''
        The processor set id (psetid) that this CPU belongs to.
        '''
        psetid = ctypes.c_int(PS_NONE)
        r = self._libc.pset_assign(PS_QUERY, 
                                   self.cpuid, 
                                   ctypes.byref(psetid))
        if r != 0:
            raise CError("pset query failed for cpu %d" % (self.cpuid))

        return psetid.value

    @property
    def active(self):
        '''
        Returns True if the calling process is executing on this CPU, 
        False otherwise.  The assumption is the calling process is
        bound to this CPU.  Using getcpuid() isn't entirely
        fool-proof,  but does not require a system call/trap like
        pset_assign(PS_QUERY) would.
        '''
        return self.cpuid == self._libc.getcpuid()

    @property
    def reported_clockrate(self):
        '''
        The clockrate in megahertz (MHz) reported to Solaris by firmware
        and recorded in the cpu_info:: kstats.
        '''
        try:
            return self._clockrate
        except AttributeError:
            self._clockrate = self.current_clock_Hz / 1e6
        return self._clockrate

    def measured_clockrate(self, sampleIntervalInSeconds=1.0):
        '''
        The clockrate in megahertz (MHz) as measured using the %tick register.
        '''
        hrt0 = self._libc.gethrtime() 
        t0 = self._tick.value
        time.sleep(sampleIntervalInSeconds)
        t1 = self._tick.value
        hrt1 = self._libc.gethrtime()
        deltaTicks = t1 - t0
        deltaSeconds = (hrt1 - hrt0) / 1e9
        return (deltaTicks / deltaSeconds) / 1e6

    def bind_process(self, curPset=PS_NONE):
        '''
        Binds the calling process to this CPU's processor set and then
        to the processor.  Returns a tuple of the previous
        bindings. If the target CPU belongs to a processor set (pset), 
        the calling process is first bound to the target pset and then
        bound to the CPU.
        '''
        prevCPU = ctypes.c_int32(PBIND_NONE)
        prevPset = ctypes.c_int32(PS_NONE)

#rcw
        global USE_PSET_BIND
        if USE_PSET_BIND == 1:
          r = self._libc.pset_bind(self.psetid, 
                                 P_PID, 
                                 P_MYID, 
                                 ctypes.byref(prevPset))
          if r is not 0:
              raise CError('failed to bind to pset %d' % self.psetid)

        r = self._libc.processor_bind(P_PID, 
                                    P_MYID, 
                                    self.cpuid, 
                                    ctypes.byref(prevCPU))
#        r = 0   #rcw ignore errors
        if r is not 0:
            print 'failed to bind process to CPU ', self.cpuid
#            raise CError('failed to bind process to CPU %d' % self.cpuid)

        return (prevCPU.value, prevPset.value)

    def unbind_process(self):
        '''
        Undoes the processor binding and then the processor set binding.
        '''
        r = self._libc.processor_bind(P_PID, P_MYID, PBIND_NONE, None)
        if r is not 0:
            print 'failed to unbind process from CPU ', self.cpuid
#            raise CError('failed to unbind process from CPU %d' % self.cpuid)
#rcw
        global USE_PSET_BIND
        if USE_PSET_BIND == 1:
           r = self._libc.pset_bind(PS_NONE, P_PID, P_MYID, None)
#rcw        r = 0
           if r is not 0:
             raise CError('failed to unbind process from pset %d' % self.psetid)


def poweradm(disable=False):
    '''
    Determine if the Solaris poweradm(1m) facility is active by parsing
    the output of poweradm.
    '''
    p = subprocess.Popen(['/usr/sbin/poweradm', 'show'], 
                         stdout=subprocess.PIPE)

    for l in p.stdout:
        if l.find('enabled') != -1:
            return True
    return False


def timestamp(epochTime=None):
    '''
    Returns an epoch-precision 24-hour clock timestamp with the format:

    YYYY-MM-DD hh:mm:ss
    '''
    if epochTime is None:
        epochTime = time.time()
        return time.strftime('%Y-%m-%d %H:%M:%S', 
                             time.localtime(epochTime))


def sample_loop(cpus, 
                interval=1.0,
                sampleCount=-1,
                reportThreshold=100.0):
    '''
    Samples the clock rate of the list of specified cpus.  The
    sampling is accomplished via round-robin scheduling and is
    dictated by the interval argument.  The sampleCount argument
    allows the caller to specify how many samples to collect.  The
    default value of -1 will allow sampling to continue until a
    keyboard interrupt is encountered or the process is killed.  The
    reportThreshold argument directs the function to only report clock
    rates when they are at or less than given threshold.
    '''

    if interval > 1:
        reportInterval = interval - 1.0
        sampleInterval = 1.0
    else:
        reportInterval = 0.0
        sampleInterval = interval

    # reportInterval == how long to wait between sweeps
    # sampleInterval == how long to sample each CPU during a sweep

    sampleIntervalInSeconds = sampleInterval / len(cpus)

    header = '%s %4s %4s %4s %4s %6s %6s %6s t=%3.0f' % (timestamp(), 
                                                         'PSET', 
                                                         'CHIP', 
                                                         'CORE', 
                                                         'CPU', 
                                                         'Mhz(r)', 
                                                         'Mhz(m)', 
                                                         'Mhz(%)', 
                                                         reportThreshold)

    fmt = '%s %4d %4d %4d %4d %6.0f %6.0f %5.0f%%'

    doBind = len(cpus) > 1

    try:
        if len(cpus) == 1:
            cpus[0].bind_process()

        while sampleCount != 0:
            sampleCount -= 1
            print header
            for cpu in cpus:
                if doBind:
                    cpu.bind_process()
                mhz_r = cpu.reported_clockrate
                mhz_m = cpu.measured_clockrate(sampleIntervalInSeconds)
                ratio = (mhz_m / mhz_r) * 100.0

                if int(ratio) <= reportThreshold:
                    print fmt % (timestamp(), 
                                 cpu.psetid, 
                                 cpu.chip_id, 
                                 cpu.core_id, 
                                 cpu.cpuid, 
                                 mhz_r, 
                                 mhz_m, 
                                 ratio)
                cpu.unbind_process()

            if reportInterval and sampleCount != 0:
                time.sleep(reportInterval)

    except KeyboardInterrupt:
        print '\n'

##
## Command-line option parsing follows
##

ACTIVE_CPUS = ['on-line', 'no-intr']              # CPU states

def get_chips(option, opt_str, value, parser):
    '''
    optparse callback function which populates the specified option destination
    key with a list of CPUs representing each chip found.
    '''
    setattr(parser.values,option.dest,
            sorted([x[0] for x in CPU.chips(states=ACTIVE_CPUS).values()]))

def get_cores(option, opt_str, value, parser):
    '''
    optparse callback function which populates the specified option destination
    key with a list of CPUs representing each core found.
    '''
    setattr(parser.values,option.dest,
            sorted([x[0] for x in CPU.cores(states=ACTIVE_CPUS).values()]))

def get_cpus(option, opt_str, value, parser):
    '''
    optparse callback function which populates the specified option destination
    key with a list of CPUs whose composition is dependent on the values given
    on the command line: 

    [ 'all', comma delimited list, range, mix of lists and ranges ]

    '''

    if value is None or value.lower() in ['all']:
        cpus = CPU.query(states=ACTIVE_CPUS)
    else:
        ids = []
        for things in value.split(','):
            if '-' in things:
                (start,stop) = things.split('-')
                ids.extend([x for x in range(int(start),int(stop)+1)])
            else:
                ids.append(int(things.strip()))
        try:
            cpus = CPU.query(ids,strictChecking=True)
        except MissingCPU, e:
            print '%s: Error.' % parser.get_prog_name(), e
            exit(-1)
            

    setattr(parser.values,option.dest,cpus)

def print_version(option, opt_str, value, parser):
    '''
    Display the current contents of Version and exit.
    '''
    print '%s version %s' % (parser.get_prog_name(),Version)
    print 'See "pydoc %s" for more information.' % (parser.get_prog_name())
    exit(0)

def parse_cmdline():
    '''
    Returns a dictionary of options specified on the command line.
    
    Uses optparse which is a deprecated module but present in
    S11uX. This can be replaced with argparse at a later date.
    '''
    import optparse
    parser = optparse.OptionParser(prog='clockrate')

    parser.add_option('-v','--version',
                      action='callback',callback=print_version,
                      help='The current version of this script (version %s)' % Version )
    
    parser.add_option('--chip',dest='cpus',
                      action='callback',callback=get_chips,
                      help='use the first active CPU found for each chip (default)')
    parser.add_option('--core',dest='cpus',
                      action='callback',callback=get_cores,
                      help='use the first active CPU found for each core')

    parser.add_option('--allcpus',dest='cpus',
                      action='callback',callback=get_cpus,
                      help='report clock rate for all active CPUs')

    parser.add_option('--cpu',dest='cpus',type='string',
                      action='callback',callback=get_cpus,
                      help='report clock rate for specified CPUs')

    parser.add_option('-i',type='float',dest='interval',default=1.0,
                      help='clock rate sample interval in seconds (default=1.0)')

    parser.add_option('-c',type='int',dest='sampleCount',default=-1,
                      help='number of samples to collect (default=-1)')

    parser.add_option('-t',type='int',dest='threshold',default=100,
                      help='report clock rates below threshold  (default=100)')

    parser.epilog = 'See "pydoc %s" for further explanation of these options.' 
    parser.epilog = parser.epilog % parser.get_prog_name()

    (options,args) = parser.parse_args()

    return options

##
## main
##

if __name__ == '__main__':

    options = parse_cmdline()

    if options.cpus is None:
        options.cpus = sorted([x[0] for x in CPU.chips(states=ACTIVE_CPUS).values()])

    sample_loop(options.cpus, 
                options.interval,
                options.sampleCount,
                options.threshold)

