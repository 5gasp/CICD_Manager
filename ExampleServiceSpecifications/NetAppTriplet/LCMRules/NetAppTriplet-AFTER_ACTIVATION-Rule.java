if (!(getCharValAsString("testsRequested").equals("yes")==true) && !(getServiceRefPropValue("migrate_nsd@OSMv15-ITAv", "serviceCharacteristicValue", "deployment_info").equals("")==true)) {
  logtext("AFTER_ACTIVATION Migration Net. App. @ ITAv: Will trigger the testing phase.");
  setCharValFromStringType("testsRequested", "yes");
  String serviceTest_ID = getCurrentServicePropValue("serviceCharacteristicValue", "testInstanceRef");
  String reqPayload = String.join("", "{\"name\":\"",getCurrentServicePropValue("name", ""),"\",\"characteristic\":[{\"name\":\"testbed_id\",\"value\":{\"value\":\"","testbed_itav","\"}},{\"name\":\"deployment_info\",\"value\":{\"value\":",getServiceRefPropValue("migrate_nsd@OSMv15-ITAv", "serviceCharacteristicValue", "deployment_info"),"}},{\"name\":\"NODS_ServiceTest_ID\",\"value\":{\"value\":\"",serviceTest_ID,"\"}},{\"name\":\"network_service_id\",\"value\":{\"value\":\"","vOBU_migration","\"}},{\"name\":\"netapp_id\",\"value\":{\"value\":\"","OdinS-NetworkApplication","\"}}],\"testSpecification\":{\"uuid\":\"",getCharValFromStringType("testSpecRef"),"\",\"id\":\"",getCharValFromStringType("testSpecRef"),"\"}}");
  setCharValFromStringType("testsRequested", "yes");
  logtext(reqPayload);
  setCharacteristicOfCurrentService("request_payload", reqPayload);
  String requestResponse = rest_block("POST","https://webhook.site/583be3b5-4144-4b91-ba0e-aff0a5fd8845","Content-Type=application/json",reqPayload);
  logtext(requestResponse);
  setCharacteristicOfCurrentService("request_response", requestResponse);
} else if (getServiceRefPropValue("migrate_nsd@OSMv15-ITAv", "serviceCharacteristicValue", "OperationalStatus").equals("failed")==true) {
  logtext("AFTER_ACTIVATION Migration Net. App. @ ITAv: The Deployment Failed. Will terminate its dependencies.");
  {
  java.util.HashMap<String,String> charvals = new java.util.HashMap<>();
  charvals.put("rollbackDeployment","true");
  charvals.put("rollbackDeployment:Completed","false");
  setServiceRefCharacteristicsValues("3GPPP Network Slice and UE Bundle @ ITAv (CFS)", charvals);
  }
  {
  java.util.HashMap<String,String> charvals = new java.util.HashMap<>();
  charvals.put("rollbackDeployment","true");
  charvals.put("rollbackDeployment:Completed","false");
  setServiceRefCharacteristicsValues("CI/CD Agent (Jenkins) - CFS", charvals);
  }
  logtext("AFTER_ACTIVATION Migration Net. App. @ ITAv: Network Bundle rollBackDeployment result");
  logtext(getServiceRefPropValue("3GPPP Network Slice and UE Bundle @ ITAv (CFS)", "serviceCharacteristicValue", "rollbackDeployment"));
  logtext("AFTER_ACTIVATION Migration Net. App. @ ITAv: Network Bundle rollBackDeployment:Completed result");
  logtext(getServiceRefPropValue("3GPPP Network Slice and UE Bundle @ ITAv (CFS)", "serviceCharacteristicValue", "rollbackDeployment:Completed"));
  logtext("AFTER_ACTIVATION Migration Net. App. @ ITAv: Jenkins rollBackDeployment result");
  logtext(getServiceRefPropValue("CI/CD Agent (Jenkins) - CFS", "serviceCharacteristicValue", "rollbackDeployment"));
  logtext("AFTER_ACTIVATION Migration Net. App. @ ITAv: Jenkins rollBackDeployment:Completed result");
  logtext(getServiceRefPropValue("CI/CD Agent (Jenkins) - CFS", "serviceCharacteristicValue", "rollbackDeployment:Completed"));
} else {
  setCharValFromStringType("testsRequested", "not_yet");
}
