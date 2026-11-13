package local.proskurnin.preview;
public class ApiEndpointTest {
 public static void main(String[] args)throws Exception{
  ApiEndpoint.validate("https://api.example.org/tv-api/v1/");ApiEndpoint.validateWeather("https://api.example.org/tv-api/v1/weather/");
  for(String url:new String[]{"http://api.example.org/tv-api/v1/","https://x@y/tv-api/v1/","https://api.example.org/tv-api/v1/?x=1","https://api.example.org/tv-api/v1/#x","https://api.example.org:0/tv-api/v1/","https://api.example.org/tv-api/v1/../"}){
   boolean rejected=false;try{ApiEndpoint.validate(url);}catch(java.io.IOException expected){rejected=true;}if(!rejected)throw new AssertionError("Unsafe endpoint accepted");
  }
  System.out.println("ApiEndpoint: passed");
 }
}
