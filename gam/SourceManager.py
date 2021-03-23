import gam
import gam_g4 as g4
import logging
import colorlog
from gam import log
from box import Box

"""
 log object for source
 use gam.source_log.setLevel(gam.RUN)
 or gam.source_log.setLevel(gam.EVENT)
 to print every run and/or event
"""
RUN = logging.INFO
EVENT = logging.DEBUG
source_log = colorlog.getLogger('gam_source')
source_log.addHandler(gam.handler)
source_log.setLevel(RUN)


class SourceManager:
    """
    Manage all the sources in the simulation.
    The function prepare_generate_primaries will be called during
    the main run loop to set the current time and source.
    """

    # G4RunManager::BeamOn takes an int as input. The max cpp int value is currently 2147483647
    # Python manage int differently (no limit), so we need to set the max value here.
    max_int = 2147483647

    def __init__(self, simulation):
        # Keep a pointer to the current simulation
        self.simulation = simulation
        # List of run times intervals
        self.run_timing_intervals = None
        self.current_run_interval = None
        # List of sources (GamSource)
        self.user_info_sources = {}
        self.sources = []
        # Keep all sources (for all threads) to avoid pointer deletion
        self.g4_sources = []
        # The source manager will be constructed at build (during ActionManager)
        # Its task is to call GeneratePrimaries and loop over the sources
        # For MT, the master_source_manager is the MasterThread
        # The g4_thread_source_managers list all master source for all threads
        self.g4_master_source_manager = None
        self.g4_thread_source_managers = []
        # internal variables
        self.particle_table = None
        # Options will be set by Simulation
        self.g4_visualisation_options = None

    def __str__(self):
        """
        str only dump the user info on a single line
        """
        v = [v.name for v in self.user_info_sources.values()]
        s = f'{" ".join(v)} ({len(self.user_info_sources)})'
        return s

    def __del__(self):
        pass

    def dump(self, level):
        n = len(self.user_info_sources)
        s = f'Number of sources: {n}'
        if level < 1:
            for source in self.user_info_sources.values():
                a = f'\n {source}'
                s += gam.indent(2, a)
        else:
            for source in self.user_info_sources.values():
                a = f'\n{source}' ## FIXME level 2 ????
                s += gam.indent(2, a)
        return s

    def get_source_info(self, name):
        if name not in self.user_info_sources:
            gam.fatal(f'The source {name} is not in the current '
                      f'list of sources: {self.user_info_sources}')
        return self.user_info_sources[name]

    def add_source(self, source_type, name):
        # auto name if needed # FIXME change ?
        if not name:
            n = len(self.user_info_sources) + 1
            name = f'source {source_type} {n}'
        # check that another element with the same name does not already exist
        gam.assert_unique_element_name(self.user_info_sources, name)
        # FIXME build it (note that the G4 counterpart of the source is not created yet)
        # it will be created by create_g4_source during build
        s = gam.UserInfo('Source', source_type, name)
        # s = gam.new_element_old('Source', source_type, name, self.simulation)
        # append to the list
        self.user_info_sources[name] = s
        # return the info
        return s

    def initialize(self, run_timing_intervals):
        self.run_timing_intervals = run_timing_intervals
        gam.assert_run_timing(self.run_timing_intervals)
        if len(self.user_info_sources) == 0:
            gam.fatal(f'No source: no particle will be generated')
        # create all source objects
        """for vu in self.user_info_sources.values():
            print('create userinfo', vu)
            source = gam.new_element(vu)
            print('created source:', source)
            self.sources[vu.name] = source
            """

    def build(self):
        print('source manager build')
        #gam.assert_run_timing(self.run_timing_intervals)
        #if len(self.sources) == 0:
        #    gam.fatal(f'No source: no particle will be generated')
        # create particles table # FIXME FIXME in physics ??
        self.particle_table = g4.G4ParticleTable.GetParticleTable()
        self.particle_table.CreateAllParticles()
        # Some sources may need a pre initialization (for example to check options)
        """for source in self.sources.values():
            print('pre init source:', source)
            source.pre_initialize()
            """
        # create the master source for the masterThread
        self.g4_master_source_manager = self.create_g4_source_manager(False)
        return self.g4_master_source_manager

    def create_g4_source_manager(self, append=True):

        # This is called by all threads

        # This object is needed here, because can only be
        # created after physics initialization
        ms = g4.GamSourceManager()

        for vu in self.user_info_sources.values():
            print('create userinfo', vu)
            source = gam.new_element(vu)
            print('created source:', source)
            source.pre_initialize()
            print('create cpp part')
            s = source.create_g4_source()
            print('add to sm')
            ms.AddSource(source.g4_source)
            print('initialize time interval')
            source.initialize(self.run_timing_intervals)

            print('append')
            #self.sources[vu.name] = source # FIXME no !!! thread
            self.sources.append(source) # FIXME no !!! thread
            self.g4_sources.append(s)
            print('sizes : ', len(self.sources), len(self.g4_sources))

        # Some sources may need a pre initialization (for example to check options)
        #for source in self.sources.values():
        #    print('pre init source:', source)
        #    source.pre_initialize()

        # set the source to the cpp side
        #for source in self.sources.values():
        #    s = source.create_g4_source()
        #    # keep pointer to avoid delete
        #    self.g4_sources.append(s)
        #    # add the source to the source manager
        #    ms.AddSource(source.g4_source)

        # initialize the source master
        ms.Initialize(self.run_timing_intervals, self.g4_visualisation_options)
        #for source in self.sources.values():
        #    s = ''
        #    if append:
        #        s = f' thread {len(self.g4_thread_source_managers) + 1}'
        #    log.debug(f'Source{s}: initialize [{source.user_info.type_name}] {source.user_info.name}')
        #    source.initialize(self.run_timing_intervals)
        # keep pointer to avoid deletion
        if append:
            self.g4_thread_source_managers.append(ms)
        return ms

    def start(self):
        # FIXME (1) later : may replace BeamOn with DoEventLoop
        # FIXME to allow better control on geometry between the different runs
        # FIXME (2) : check estimated nb of particle, warning if too large
        # start the master thread (only main thread)
        self.g4_master_source_manager.StartMainThread()
