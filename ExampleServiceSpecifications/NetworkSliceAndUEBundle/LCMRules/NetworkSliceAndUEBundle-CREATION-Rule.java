setCharValFromStringType("slice:Name", getServiceRefPropValue("3GPPP Network Slice @ ITAv (CFS)", "serviceCharacteristicValue", "Id"));
setCharValFromStringType("slice:isConfigured", getServiceRefPropValue("3GPPP Network Slice @ ITAv (CFS)", "serviceCharacteristicValue", "isConfigured"));
{
java.util.HashMap<String,String> charvals = new java.util.HashMap<>();
createServiceRefIf("3GPPP UE @ ITAv (CFS)", getCharValFromStringType("slice:isConfigured").equals("true")==true, charvals);
}
