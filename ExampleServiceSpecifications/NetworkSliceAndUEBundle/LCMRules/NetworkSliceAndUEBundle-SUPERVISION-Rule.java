setCharValFromStringType("slice:Name", getServiceRefPropValue("3GPPP Network Slice @ ITAv (CFS)", "serviceCharacteristicValue", "Id"));
setCharValFromStringType("slice:isConfigured", getServiceRefPropValue("3GPPP Network Slice @ ITAv (CFS)", "serviceCharacteristicValue", "isConfigured"));
setCharValFromStringType("ue:Supi", getServiceRefPropValue("3GPPP UE @ ITAv (CFS)", "serviceCharacteristicValue", "Supi"));
setCharValFromStringType("ue:isConfigured", getServiceRefPropValue("3GPPP UE @ ITAv (CFS)", "serviceCharacteristicValue", "isConfigured"));
if (getCharValAsString("rollbackDeployment").equals("true")==true && getCharValAsString("rollbackDeployment:Completed").equals("false")==true) {
  {
  java.util.HashMap<String,String> charvals = new java.util.HashMap<>();
  charvals.put("Operational State","DISABLED");
  setServiceRefCharacteristicsValues("3GPPP Network Slice @ ITAv (CFS)", charvals);
  }
  {
  java.util.HashMap<String,String> charvals = new java.util.HashMap<>();
  charvals.put("Operational State","DISABLED");
  setServiceRefCharacteristicsValues("3GPPP UE @ ITAv (CFS)", charvals);
  }
} else if ((getCharValAsString("ue:isConfigured").equals("false")==true && getCharValAsString("slice:isConfigured").equals("false")==true) && getCharValAsString("rollbackDeployment").equals("true")==true) {
  setCharValFromStringType("rollbackDeployment:Completed", "true");
}
