import math

from m5.defines import buildEnv
from m5.util import fatal, panic

from m5.objects import *

class MyCacheSystem(RubySystem):

    def __init__(self):
        if buildEnv['PROTOCOL'] != 'MI_example':
            fatal("This system assumes MI_example!")

        super(MyCacheSystem, self).__init__()

    def setup(self, system, cpus, mem_ctrls):
        # Ruby's global network.
        self.network = MyNetwork(self)

        # MI example uses 5 virtual networks
        self.number_of_virtual_networks = 5
        self.network.number_of_virtual_networks = 5

        self.controllers = \
            [L1Cache(system, self, cpu) for cpu in cpus] + \
            [DirController(self, system.mem_ranges, mem_ctrls)]

        # Create one sequencer per CPU.
        self.sequencers = [RubySequencer(version = i,
                                # I/D cache is combined and grab from ctrl
                                dcache = self.controllers[i].cacheMemory,
                                clk_domain = self.controllers[i].clk_domain,
                                ) for i in range(len(cpus))]

        for i,c in enumerate(self.controllers[0:len(cpus)]):
            c.sequencer = self.sequencers[i]

        self.num_of_sequencers = len(self.sequencers)

        # Create the network and connect the controllers.
        self.network.connectControllers(self.controllers)
        self.network.setup_buffers()

        # Set up a proxy port for the system_port.
        self.sys_port_proxy = RubyPortProxy()
        system.system_port = self.sys_port_proxy.slave

        # Connect the system to Ruby
        for i,cpu in enumerate(cpus):
            self.sequencers[i].connectCpuPorts(cpu)

class L1Cache(L1Cache_Controller):

    _version = 0
    @classmethod
    def versionCount(cls):
        cls._version += 1
        return cls._version - 1

    def __init__(self, system, ruby_system, cpu):

        super(L1Cache, self).__init__()

        self.version = self.versionCount()
        # This is the cache memory object that stores the cache data and tags
        self.cacheMemory = RubyCache(size = '32kB',
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
        self.requestFromCache = MessageBuffer(ordered = True)
        self.requestFromCache.master = ruby_system.network.slave
        self.responseFromCache = MessageBuffer(ordered = True)
        self.responseFromCache.master = ruby_system.network.slave
        self.forwardToCache = MessageBuffer(ordered = True)
        self.forwardToCache.slave = ruby_system.network.master
        self.responseToCache = MessageBuffer(ordered = True)
        self.responseToCache.slave = ruby_system.network.master

class DirController(Directory_Controller):

    _version = 0
    @classmethod
    def versionCount(cls):
        cls._version += 1 # Use count for this particular type
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
        self.requestToDir = MessageBuffer(ordered = True)
        self.requestToDir.slave = ruby_system.network.master
        self.dmaRequestToDir = MessageBuffer(ordered = True)
        self.dmaRequestToDir.slave = ruby_system.network.master

        self.responseFromDir = MessageBuffer()
        self.responseFromDir.master = ruby_system.network.slave
        self.dmaResponseFromDir = MessageBuffer(ordered = True)
        self.dmaResponseFromDir.master = ruby_system.network.slave
        self.forwardFromDir = MessageBuffer()
        self.forwardFromDir.master = ruby_system.network.slave
        self.requestToMemory = MessageBuffer()
        self.responseFromMemory = MessageBuffer()

class MyNetwork(SimpleNetwork):

    def __init__(self, ruby_system):
        super(MyNetwork, self).__init__()
        self.netifs = []
        self.ruby_system = ruby_system

    def connectControllers(self, controllers):

        # Create one router/switch per controller in the system
        self.routers = [Switch(router_id = i) for i in range(len(controllers))]

        # Make a link from each controller to the router.
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
                self.int_links.append(SimpleIntLink(link_id = link_count,
                                                    src_node = ri,
                                                    dst_node = rj))
