
import types
import os
import shutil
import json
from tornado import web, gen
from RESTDIRAC.RESTSystem.Base.RESTHandler import WErr, WOK, TmpDir, RESTHandler, DummyRESTHandler
from DIRAC.Core.DISET.RPCClient import RPCClient
from DIRAC.WorkloadManagementSystem.Client.SandboxStoreClient import SandboxStoreClient
from DIRAC.Core.Utilities import List, CFG
from DIRAC.Core.Utilities.JDL import loadJDLAsCFG, dumpCFGAsJDL

class MqGwHandler( DummyRESTHandler ):

  ROUTE = "/mqgw(?:/([0-9]+))?"
  REQUIRE_ACCESS = False


  @web.asynchronous
  @gen.engine
  def get( self, jid ):
    data = {'jid' : jid}
    self.finish( data )
