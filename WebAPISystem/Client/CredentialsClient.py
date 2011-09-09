from DIRAC import S_OK, S_ERROR
from DIRAC.Core.DISET.RPCClient import RPCClient
from DIRAC.Core.Utilities.DictCache import DictCache

class CredentialsClient:

  CONSUMER_GRACE_TIME = 3600
  REQUEST_GRACE_TIME = 900

  def __init__( self, RPCFunctor = None ):
    if not RPCFunctor:
      self.__RPCFunctor = RPCClient
    else:
      self.__RPCFunctor = RPCFunctor
    self.__tokens = DictCache()
    self.__requests = DictCache()
    self.__consumers = DictCache( deleteFunction = self.__cleanConsumerCache )

  def __getRPC( self ):
    return self.__RPCFunctor( "WebAPI/Credentials" )

  def __cleanReturn( self, result ):
    if 'rpcStub' in result:
      result.pop( 'rpcStub' )
    return result

  ##
  # Consumer
  ##

  def generateConsumerPair( self, consumerKey = "" ):
    result = self.__getRPC().generateConsumerPair( consumerKey )
    if not result[ 'OK' ]:
      return self.__cleanReturn( result )
    consumerKey, secret = result[ 'Value' ]
    self.__consumers.add( consumerKey, self.CONSUMER_GRACE_TIME, ( consumerKey, secret ) )
    return self.__cleanReturn( result )

  def getConsumerSecret( self, consumerKey ):
    cData = self.__consumers.get( consumerKey )
    if cData:
      return cData[1]
    result = self.__getRPC().getConsumerSecret( consumerKey )
    if not result[ 'OK' ]:
      return self.__cleanReturn( result )
    self.__consumers.add( consumerKey, self.CONSUMER_GRACE_TIME, ( consumerKey, result[ 'Value' ] ) )
    return self.__cleanReturn( result )

  def deleteConsumer( self, consumerKey ):
    self.__consumers.delete( consumerKey )
    result = self.__getRPC().deleteConsumer( consumerKey )
    if result[ 'OK' ]:
      self.__cleanConsumerCache( ( consumerKey, "" ) )
    return self.__cleanReturn( result )

  def getAllConsumers( self ):
    result = self.__getRPC().getAllConsumers()
    if not result[ 'OK' ]:
      return self.__cleanReturn( result )
    for record in result[ 'Value' ]:
      self.__consumers.add( record[0], self.CONSUMER_GRACE_TIME, record[1] )
    return self.__cleanReturn( result )

  def __cleanConsumerCache( self, cData ):
    consumerKey = cData[0]
    for dc in ( self.__tokens, self.__requests ):
      cKeys = dc.getKeys()
      for cKey in cKeys:
        if cKey[0] == consumerKey:
          dc.delete( cKey )

  ##
  # Requests
  ##

  def generateRequest( self, consumerKey ):
    result = self.__getRPC().generateRequest( consumerKey )
    if not result[ 'OK' ]:
      return self.__cleanReturn( result )
    requestPair = result[ 'Value' ]
    self.__requests.add( ( consumerKey, requestPair[0] ), self.REQUEST_GRACE_TIME, requestPair[1] )
    return self.__cleanReturn( result )

  def getRequestSecret( self, consumerKey, request ):
    cKey = ( consumerKey, request )
    secret = self.__requests.get( cKey )
    if secret:
      return S_OK( secret )
    result = self.__getRPC().getRequestSecret( consumerKey, request )
    if not result[ 'OK' ]:
      return self.__cleanReturn( result )
    self.__tokens.add( cKey, result[ 'lifeTime' ] - 5, result[ 'Value' ] )
    return self.__cleanReturn( result )

  def deleteRequest( self, request ):
    result = self.__getRPC().deleteRequest( request )
    if not result[ 'OK' ]:
      return self.__cleanReturn( result )
    cKeys = self.__requests.getKeys()
    for cKey in cKeys:
      if cKey[1] == request:
        self.__requests.delete( cKey )
    return self.__cleanReturn( result )

  ##
  # Verifiers
  ##

  def generateVerifier( self, userDN, userGroup, consumerKey, request ):
    result = self.__getRPC().generateVerifier( userDN, userGroup, consumerKey, request )
    return self.__cleanReturn( result )

  def getVerifierUserAndGroup( self, consumerKey, request, verifier ):
    result = self.__getRPC().getVerifierUserAndGroup( consumerKey, request, verifier )
    return self.__cleanReturn( result )

  def expireVerifier( self, consumerKey, request, verifier ):
    result = self.__getRPC().expireVerifier( consumerKey, request, verifier )
    return self.__cleanReturn( result )

  def getVerifier( self, consumerKey, request ):
    result = self.__getRPC().getVerifier( consumerKey, request )
    return self.__cleanReturn( result )

  ##
  # Tokens
  ##

  def generateToken( self, consumerKey, request, verifier, lifeTime = 86400 ):
    result = self.__getRPC().generateToken( consumerKey, request, verifier, lifeTime )
    if not result[ 'OK' ]:
      return self.__cleanReturn( result )
    tokenData = result[ 'Value' ]
    cKey = ( consumerKey, tokenData[ 'token' ] )
    self.__tokens.add( cKey, lifeTime - 5, tokenData )
    return S_OK( tokenData )

  def getTokenData( self, consumerKey, token ):
    cKey = ( consumerKey, token )
    tokenData = self.__tokens.get( cKey )
    if tokenData:
      return S_OK( tokenData )
    result = self.__getRPC().getTokenSecret( consumerKey, token )
    if not result[ 'OK' ]:
      return self.__cleanReturn( result )
    tokenData = result[ 'Value' ]
    self.__tokens.add( cKey, tokenData[ 'lifeTime' ] - 5, tokenData )
    return self.__cleanReturn( result )

  def revokeUserToken( self, userDN, userGroup, token ):
    result = self.__getRPC().revokeUserToken( userDN, userGroup, token )
    if not result[ 'OK' ]:
      return self.__cleanReturn( result )
    cKeys = self.__tokens.getKeys()
    for cKey in cKeys:
      if cKey[0] == userDN and cKey[1] == userGroup and cKey[3] == token:
        self.__tokens.delete( cKey )
    return self.__cleanReturn( result )

  def revokeToken( self, token ):
    result = self.__getRPC().revokeToken( token )
    if not result[ 'OK' ]:
      return self.__cleanReturn( result )
    cKeys = self.__tokens.getKeys()
    for cKey in cKeys:
      if cKey[3] == token:
        self.__tokens.delete( cKey )
    return self.__cleanReturn( result )

  def cleanExpired( self ):
    return self.__getRPC().cleanExpired()

  def getTokens( self, condDict = {} ):
    result = self.__getRPC().getTokens( condDict )
    if not result[ 'OK' ]:
      return self.__cleanReturn( result )
    params = result[ 'Value' ][ 'Parameters']
    data = result[ 'Value' ][ 'Records' ]
    consumerKey = "unknown"
    token = unknown
    lifeTime = 0
    for record in data:
      tokenData = {}
      for iPos in range( len( params ) ):
        if params[iPos] == "UserDN":
          tokenData[ 'userDN' ] = record[iPos]
        elif params[iPos] == "UserGroup":
          tokenData[ 'userGroup' ] = record[iPos]
        elif params[iPos] == "ConsumerKey":
          consumerKey = record[iPos]
        elif params[iPos] == "Token":
          token = record[iPos]
        elif params[iPos] == "Secret":
          tokenData[ 'secret' ] = record[iPos]
        elif params[iPos] == "LifeTime":
          tokenData[ 'lifeTime' ] = record[iPos]
          lifeTime = record[ iPos ]
      self.__tokens.add( ( consumerKey, token ), tokenData[ 'lifeTime' ], tokenData )
    return self.__cleanReturn( result )




