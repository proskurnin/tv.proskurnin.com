package local.proskurnin.preview;
import org.json.*;import java.util.*;
/** Availability is catalog evidence, not a user's subscription or viewing history. */
final class MovieAvailability {
 static final String[] TYPES={"flatrate","rent","buy","free","ads"},LABELS={"подписка","аренда","покупка","бесплатно","с рекламой"};
 static JSONArray offers(JSONObject root)throws JSONException{JSONObject ru=root.optJSONObject("results");ru=ru==null?null:ru.optJSONObject("RU");LinkedHashMap<Integer,JSONObject> rows=new LinkedHashMap<>();if(ru==null)return new JSONArray();for(int k=0;k<TYPES.length;k++){JSONArray list=ru.optJSONArray(TYPES[k]);if(list==null)continue;for(int i=0;i<Math.min(100,list.length());i++){JSONObject p=list.optJSONObject(i);if(p==null||p.optInt("provider_id")<=0||p.optString("provider_name").isEmpty())continue;int id=p.getInt("provider_id");JSONObject row=rows.get(id);if(row==null){row=new JSONObject().put("id",id).put("name",p.getString("provider_name")).put("offer",LABELS[k]);rows.put(id,row);}else if(!row.getString("offer").contains(LABELS[k]))row.put("offer",row.getString("offer")+", "+LABELS[k]);}}JSONArray out=new JSONArray();for(JSONObject row:rows.values())out.put(row);return out;}
 static int cinema(String name){String n=name.toLowerCase(Locale.ROOT);if(n.contains("kinopoisk")||n.contains("кинопоиск"))return 0;if(n.equals("ivi")||n.equals("иви"))return 1;if(n.equals("okko")||n.equals("окко"))return 2;if(n.contains("premier")||n.contains("премьер"))return 3;if(n.equals("kion")||n.equals("кион"))return 6;return -1;}
}
