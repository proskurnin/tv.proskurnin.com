package local.proskurnin.preview;
/** Missing days remain gaps; valid samples are never fabricated or interpolated. */
final class RatesSparkline {
 static boolean valid(double v){return Double.isFinite(v)&&v>0;}
 static int count(double[] values){int n=0;if(values!=null)for(double v:values)if(valid(v))n++;return n;}
 static float[] normalize(double[] values){if(values==null||values.length!=7||count(values)<2)return null;double min=Double.POSITIVE_INFINITY,max=0;for(double v:values)if(valid(v)){min=Math.min(min,v);max=Math.max(max,v);}float[] out=new float[7];for(int i=0;i<7;i++)out[i]=!valid(values[i])?Float.NaN:max==min?.5f:(float)(1-(values[i]-min)/(max-min));return out;}
}
