if (getCharValAsString("rollbackDeployment").equals("true")==true && getCharValAsString("rollbackDeployment:Completed").equals("false")==true) {
  {
  java.util.HashMap<String,String> charvals = new java.util.HashMap<>();
  charvals.put("rollbackDeployment","true");
  charvals.put("rollbackDeployment:Completed","false");
  setServiceRefCharacteristicsValues("CI/CD Agent (Jenkins) - RFS", charvals);
  }
}
