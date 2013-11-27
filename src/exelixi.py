#!/usr/bin/env python
# encoding: utf-8

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# author: Paco Nathan
# https://github.com/ceteri/exelixi


from argparse import ArgumentParser
from ga import APP_NAME
from json import loads
from service import Worker
from urllib2 import urlopen


######################################################################
## utilities

def get_master_state (master_uri):
    """get current state, represented as JSON, from the Mesos master"""
    response = urlopen("http://" + master_uri + "/master/state.json")
    return loads(response.read())


def get_master_leader (master_uri):
    """get the host:port for the Mesos master leader"""
    state = get_master_state(master_uri)
    return state["leader"].split("@")[1]


def get_slave_list (master_uri):
    """get a space-separated list of slave IP addr"""
    state = get_master_state(get_master_leader(master_uri))
    slaves = state["slaves"]
    return " ".join([ s["pid"].split("@")[1].split(":")[0] for s in slaves ])


if __name__=='__main__':
    parser = ArgumentParser(prog="Exelixi", usage="one of the operational modes shown below...", add_help=True,
                            description="Exelixi, a distributed framework for genetic algorithms, based on Apache Mesos")

    group1 = parser.add_argument_group("Mesos Framework", "run as a Framework on an Apache Mesos cluster")
    group1.add_argument("-m", "--master", metavar="HOST:PORT", nargs=1,
                        help="location for one of the masters")
    group1.add_argument("-e", "--executors", nargs=1, type=int, default=1,
                        help="number of Executors to be launched")

    group2 = parser.add_argument_group("Standalone Framework", "run as a Framework in standalone mode")
    group2.add_argument("-s", "--slaves", nargs="+", metavar="HOST:PORT",
                        help="list of slaves (HOST:PORT) on which to run Executors")

    group3 = parser.add_argument_group("Mesos Executor", "run as an Apache Mesos executor (using no arguments)")

    group4 = parser.add_argument_group("Standalone Executor", "run as an Executor in standalone mode")
    group4.add_argument("-p", "--port", nargs=1, metavar="PORT",
                        help="port number to use for this service")

    group5 = parser.add_argument_group("Nodes", "enumerate the slave nodes in an Apache Mesos cluster")
    group5.add_argument("-n", "--nodes", nargs=1, metavar="HOST:PORT",
                        help="location for one of the masters")

    parser.add_argument("-f", "--feature", nargs=1, metavar="PKG.CLASS", default="run.FeatureFactory",
                        help="extension of FeatureFactory class to use for GA parameters and customizations")

    args = parser.parse_args()
    #print args

    # interpret arguments based on the different operational modes

    if args.nodes:
        print get_slave_list(args.nodes[0])

    elif args.master:
        print "%s running a Framework atop an Apache Mesos cluster" % (APP_NAME),
        print "with master %s and %d executor(s)" % (args.master[0], args.executors)

        if args.feature:
            print "  using %s for the GA parameters and customizations" % (args.feature)

        from sched import MesosScheduler

        master_uri = get_master_leader(args.master[0])
        ## NB: TODO make path relative
        exe_path = "/home/ubuntu/exelixi-master/src/exelixi.py"

        driver = MesosScheduler.start_framework(master_uri, exe_path, args.executors)
        MesosScheduler.stop_framework(driver)

    elif args.slaves:
        print "%s running a Framework in standalone mode" % (APP_NAME),
        print "with slave(s) %s" % (args.slaves)

        if args.feature:
            print "  using %s for the GA parameters and customizations" % (args.feature)

            ## NB: TODO begin Framework orchestration via REST services

    elif args.port:
        print "%s running an Executor service on port %s" % (APP_NAME, args.port[0])

        # launch service
        try:
            svc = Worker(port=int(args.port[0]))
            svc.start()
        except KeyboardInterrupt:
            pass

    else:
        print "%s running an Executor atop an Apache Mesos cluster" % (APP_NAME)

        from sched import MesosExecutor

        try:
            MesosExecutor.run_executor()
        except KeyboardInterrupt:
            pass