package local.proskurnin.preview;
/** Seven actual daily samples, no invented values or interpolation across missing days. */
final class RatesSparkline {
 static float[] normalize(double[] values){if(values==null||values.length!=7)return null;double min=Double.POSITIVE_INFINITY,max=0;for(double value:values){if(!Double.isFinite(value)||value<=0)return null;min=Math.min(min,value);max=Math.max(max,value);}float[] out=new float[7];for(int i=0;i<7;i++)out[i]=max==min?.5f:(float)(1-(values[i]-min)/(max-min));return out;}
}
