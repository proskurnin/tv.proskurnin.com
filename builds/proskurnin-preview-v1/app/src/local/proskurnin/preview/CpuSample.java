package local.proskurnin.preview;
final class CpuSample {
 final long total,idle;CpuSample(long t,long i){total=t;idle=i;}
 static CpuSample parse(String line){String[] v=line.trim().split("\\s+");if(v.length<5||!v[0].equals("cpu"))throw new IllegalArgumentException();long total=0,idle=0;for(int i=1;i<Math.min(v.length,9);i++){long n=Long.parseLong(v[i]);if(n<0)throw new IllegalArgumentException();total+=n;if(i==4||i==5)idle+=n;}return new CpuSample(total,idle);}
 static int usage(CpuSample old,CpuSample now){if(old==null||now.total<=old.total||now.idle<old.idle)return -1;long total=now.total-old.total,idle=now.idle-old.idle;if(idle>total)return -1;return (int)Math.round(100.0*(total-idle)/total);}
}
