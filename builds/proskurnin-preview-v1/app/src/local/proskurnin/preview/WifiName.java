package local.proskurnin.preview;
final class WifiName {
 static String clean(String value){
  if(value==null)return "";String s=value.trim();
  if(s.length()>=2&&s.startsWith("\"")&&s.endsWith("\""))s=s.substring(1,s.length()-1);
  if(s.isEmpty()||s.equalsIgnoreCase("<unknown ssid>")||s.equalsIgnoreCase("unknown ssid")||s.equals("0x"))return "";
  StringBuilder out=new StringBuilder();
  for(int i=0;i<s.length();i++){char c=s.charAt(i);if(!Character.isISOControl(c)&&Character.getType(c)!=Character.FORMAT)out.append(c);}
  return out.toString();
 }
}
