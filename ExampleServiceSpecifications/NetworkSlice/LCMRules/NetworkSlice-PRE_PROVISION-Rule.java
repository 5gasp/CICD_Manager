{
java.util.HashMap<String,String> charvals = new java.util.HashMap<>();
charvals.put("_CR_SPEC",String.format("""
apiVersion: av.it.pt/v1
kind: ITAvNetSlice
spec:
  itav-netslice:
    id: "%s"
    administrativeState: "UNLOCKED"
    operationalState: "%s"
    coverageArea: "IT"
    sstSnssai:
      sst: 1
      sd: "123456"
    dnn: "%s"
    priorityLabel: 100
    ueMobilityLevel: "stationary"
    reliability: 99.999
    maxPacketSize:
      maximumSize: 150
    latency:
      dl: 5
      ul: 5
    delayToleranceSupport: "NOT_SUPPORTED"
    deterministicCommunication:
      dl:
        availability: "SUPPORTED"
        periodicity: 10
      ul:
        availability: "SUPPORTED"
        periodicity: 10
    dlThroughputPerUE:
      guaranteedThroughput: 240
      maximumThroughput: 600
    ulThroughputPerUE:
      guaranteedThroughput: 240
      maximumThroughput: 600

    dlThroughputPerSlice:
      guaranteedThroughput: 5000
      maximumThroughput: 5000
    ulThroughputPerSlice:
      guaranteedThroughput: 5000
      maximumThroughput: 5000
    termDensity: 10
    maxNumberOfPduSessions: 20
    maxNumberOfUes: 25
    n6Protection: '[{"type":"PCC Rule","name":"rule_any"}]'

  itav-netslice-enforcement:
    retryOnFail: true
    maxRetries: 5
    waitTimeBeforeRetrying: 10
"""
, getCharValAsString("Id"), getCharValAsString("Operational State"), getCharValAsString("Network Slice Subnet Ref (DNN)")));
setServiceRefCharacteristicsValues("3GPPP Network Slice @ ITAv (RFS)", charvals);
}
