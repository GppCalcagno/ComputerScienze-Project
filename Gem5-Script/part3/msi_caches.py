import math

from m5.defines import buildEnv
from m5.util import fatal, panic

from m5.objects import *

class MyCacheSystem(RubySystem):

    def __init__(self):
        if buildEnv['PROTOCOL'] != 'MSI':
            fatal("This system assumes MSI from learning gem5!")

        super(MyCacheSystem, self).__init__()

    def setup(self, system, cpus, mem_ctrls):
        # Ruby's global network.
        self.network = MyNetwork(self)

        self.number_of_virtual_networks = 3
        self.network.number_of_virtual_networks = 3

        self.controllers = \
            [L1Cache(system, self, cpu) for cpu in cpus] + \
            [DirController(self, system.mem_ranges, mem_ctrls)]

        self.sequencers = [RubySequencer(version = i,
                                dcache = self.controllers[i].cacheMemory,
                                clk_domain = self.controllers[i].clk_domain,
                                ) for i in range(len(cpus))]


        for i,c in enumerate(self.controllers[0:len(self.sequencers)]):
            c.sequencer = self.sequencers[i]

        self.num_of_sequencers = len(self.sequencers)

        self.network.connectControllers(self.controllers)
        self.network.setup_buffers()

        self.sys_port_proxy = RubyPortProxy()
        system.system_port = self.sys_port_proxy.slave

        # Connect system to Ruby
        for i,cpu in enumerate(cpus):
            self.sequencers[i].connectCpuPorts(cpu)


class L1Cache(L1Cache_Controller):

    _version = 0
    @classmethod
    def versionCount(cls):
        cls._version += 1
        return cls._version - 1

    def __init__(self, system, ruby_system, cpu):
        """CPUs are needed to grab the clock domain and system is needed for
           the cache block size.
        """
        super(L1Cache, self).__init__()

        self.version = self.versionCount()
        # This is the cache memory object that stores the cache data and tags
        self.cacheMemory = RubyCache(size = '16kB',
                               assoc = 8,
                               start_index_bit = self.getBlockSizeBits(system))
        self.clk_domain = cpu.clk_domain
        self.send_evictions = self.sendEvicts(cpu)
        self.ruby_system = ruby_system
        self.connectQueues(ruby_system)

    def getBlockSizeBits(self, system):
        bits = int(math.log(system.cache_line_size, 2))
        if 2**bits != system.cache_line_size.value:
            panic("Cache line size not a power of 2!")
        return bits

    def sendEvicts(self, cpu):
        if type(cpu) is DerivO3CPU or \
           buildEnv['TARGET_ISA'] in ('x86', 'arm'):
            return True
        return False

    def connectQueues(self, ruby_system):
        self.mandatoryQueue = MessageBuffer()
        self.requestToDir = MessageBuffer(ordered = True)
        self.requestToDir.master = ruby_system.network.slave
        self.responseToDirOrSibling = MessageBuffer(ordered = True)
        self.responseToDirOrSibling.master = ruby_system.network.slave
        self.forwardFromDir = MessageBuffer(ordered = True)
        self.forwardFromDir.slave = ruby_system.network.master
        self.responseFromDirOrSibling = MessageBuffer(ordered = True)
        self.responseFromDirOrSibling.slave = ruby_system.network.master

class DirController(Directory_Controller):

    _version = 0
    @classmethod
    def versionCount(cls):
        cls._version += 1
        return cls._version - 1

    def __init__(self, ruby_system, ranges, mem_ctrls):

        if len(mem_ctrls) > 1:
            panic("This cache system can only be connected to one mem ctrl")
        super(DirController, self).__init__()
        self.version = self.versionCount()
        self.addr_ranges = ranges
        self.ruby_system = ruby_system
        self.directory = RubyDirectoryMemory()
        # Connect this directory to the memory side.
        self.memory = mem_ctrls[0].port
        self.connectQueues(ruby_system)

    def connectQueues(self, ruby_system):
        self.requestFromCache = MessageBuffer(ordered = True)
        self.requestFromCache.slave = ruby_system.network.master
        self.responseFromCache = MessageBuffer(ordered = True)
        self.responseFromCache.slave = ruby_system.network.master

        self.responseToCache = MessageBuffer(ordered = True)
        self.responseToCache.master = ruby_system.network.slave
        self.forwardToCache = MessageBuffer(ordered = True)
        self.forwardToCache.master = ruby_system.network.slave

        self.requestToMemory = MessageBuffer()
        self.responseFromMemory = MessageBuffer()

class MyNetwork(SimpleNetwork):
    """A simple point-to-point network. This doesn't not use garnet.
    """

    def __init__(self, ruby_system):
        super(MyNetwork, self).__init__()
        self.netifs = []
        self.ruby_system = ruby_system

    def connectControllers(self, controllers):

        # Create one router/switch per controller in the system
        self.routers = [Switch(router_id = i) for i in range(len(controllers))]

        # Make a link from each controller to the router. The link goes
        # externally to the network.
        self.ext_links = [SimpleExtLink(link_id=i, ext_node=c,
                                        int_node=self.routers[i])
                          for i, c in enumerate(controllers)]

        # Make an "internal" link (internal to the network) between every pair
        # of routers.
        link_count = 0
        self.int_links = [] 
        for ri in self.routers:     
            for rj in self.routers:
                if ri == rj: continue
               	link_count += 1
               	self.int_links.append(SimpleIntLink(link_id = link_count,src_node = ri, dst_node = rj))
