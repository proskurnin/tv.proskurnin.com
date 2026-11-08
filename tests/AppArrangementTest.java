package local.proskurnin.preview;
import java.util.*;

public final class AppArrangementTest {
 static void check(boolean value) { if (!value) throw new AssertionError(); }
 static void eq(Object a, Object b) { if (!a.equals(b)) throw new AssertionError(a+" != "+b); }
 static List<String> list(String... values) { return Arrays.asList(values); }
 static void invariant(AppArrangement a, Collection<String> installed) {
  ArrayList<String> all=new ArrayList<>(a.home);all.addAll(a.apps);all.addAll(a.other);
  check(a.home.size()<=6);eq(new HashSet<>(all).size(),all.size());eq(new HashSet<>(all),new HashSet<>(installed));
 }
 public static void main(String[] args) {
  AppArrangement a=new AppArrangement();a.home.addAll(list("a","b","c","d","e","f"));
  List<String> installed=list("a","b","c","d","e","f","g","h","i");a.reconcile(installed);
  check(!a.pin("g",-1));eq(a.home,list("a","b","c","d","e","f"));
  check(a.pin("g",2));eq(a.home,list("a","b","g","d","e","f"));check(a.apps.contains("c"));invariant(a,installed);
  check(a.hide("b","h"));eq(a.home,list("a","h","g","d","e","f"));eq(a.other,list("b"));invariant(a,installed);
  check(a.hide("a",null));eq(a.home.size(),5);check(a.pin("b",-1));eq(a.home.get(5),"b");check(!a.other.contains("b"));invariant(a,installed);
  check(!a.hide("h","b"));check(!a.hide("h","missing"));
  a.restore("a");check(a.apps.contains("a"));a.unpin("b");check(a.apps.contains("b"));invariant(a,installed);
  AppArrangement original=a.copy();AppArrangement.move(a.apps,0,a.apps.size()-1);check(!a.apps.equals(original.apps));a=original.copy();eq(a.apps,original.apps);
  check(a.pin("h",2));eq(a.home.get(2),"h");invariant(a,installed);
  for(String pkg:new ArrayList<>(a.home))check(a.hide(pkg,null));check(a.home.isEmpty());invariant(a,installed);
  check(a.pin(a.other.get(0),-1));eq(a.home.size(),1);invariant(a,installed);
  a.home.add(a.home.get(0));a.other.add("missing");a.apps.add("");a.reconcile(installed);invariant(a,installed);
  installed=list("a","c","e","f","g","h","i","new");a.reconcile(installed);invariant(a,installed);eq(a.apps.get(a.apps.size()-1),"new");
  check(!a.pin("missing",0));
  for(int count=0;count<=6;count++){float width=count*260+Math.max(0,count-1)*25;check(AppArrangement.homeLeft(count)*2+width==1920);}
  eq(AppArrangement.next(5,8,20,6),7);eq(AppArrangement.next(7,8,19,6),1);eq(AppArrangement.next(5,8,22,6),5);eq(AppArrangement.next(0,0,20,6),0);
  // Home uses exactly the same reorder operation as the drawer: 1–6 favorites.
  for(int count=1;count<=6;count++){
   ArrayList<String> favorites=new ArrayList<>(list("a","b","c","d","e","f").subList(0,count));
   ArrayList<String> before=new ArrayList<>(favorites);
   int pos=AppArrangement.reorder(favorites,0,22);eq(pos,count>1?1:0);eq(favorites.get(pos),"a");
   eq(AppArrangement.reorder(favorites,pos,19),pos);eq(AppArrangement.reorder(favorites,pos,20),pos);
   eq(AppArrangement.reorder(favorites,pos,21),0);eq(favorites,before);pos=0;
   for(int step=0;step<8;step++)pos=AppArrangement.reorder(favorites,pos,22);
   eq(pos,count-1);eq(favorites.get(pos),"a");
  }
  // Long sequences keep the three lists disjoint and never exceed the home limit.
  Random random=new Random(133);for(int n=0;n<2000;n++){String pkg=installed.get(random.nextInt(installed.size()));switch(random.nextInt(5)){case 0:a.pin(pkg,random.nextInt(8)-1);break;case 1:a.hide(pkg,null);break;case 2:a.restore(pkg);break;case 3:a.unpin(pkg);break;default:AppArrangement.move(a.apps,0,random.nextInt(20));}invariant(a,installed);}
  System.out.println("AppArrangement: migration, replacement, folder, cancel, empty home, uninstall, focus, centering and 2000 mixed operations passed");
 }
}
