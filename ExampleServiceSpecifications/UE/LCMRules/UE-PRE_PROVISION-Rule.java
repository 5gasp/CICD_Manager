{
java.util.HashMap<String,String> charvals = new java.util.HashMap<>();
charvals.put("_CR_SPEC",String.format("""
apiVersion: av.it.pt/v1
kind: ITAvUE
spec:
  itav-ue:
    operationalState: "%s"
    supi: "%s"
    requestedNSSAI:
      sst: 1
      sd: "123456"
    defaultNSSAI:
      sst: 1
      sd: "123456"
    dnn: "%s"
    pduSession:
      type: "IPv4v6"
    sessionAmbr:
      uplink: 4000000
      downlink: 4000000
  itav-ue-enforcement:
    retryOnFail: true
    maxRetries: 5
    waitTimeBeforeRetrying: 10

"""
, getCharValAsString("Operational State"), getCharValAsString("Supi"), getCharValAsString("DNN")));
setServiceRefCharacteristicsValues("3GPPP UE @ ITAv (RFS)", charvals);
}
