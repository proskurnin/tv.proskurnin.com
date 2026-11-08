package local.proskurnin.preview;
import android.app.*;import android.content.*;import android.graphics.Typeface;import android.graphics.drawable.*;import android.view.*;import android.widget.*;
/** Launcher-owned dialogs only. Native controls retain DPAD, Back and accessibility semantics. */
final class LauncherDialogs {
 static int dp(Context c,int n){return Math.round(n*c.getResources().getDisplayMetrics().density);}
 static GradientDrawable shape(Context c,int fill,int stroke,int radius){GradientDrawable d=new GradientDrawable();d.setColor(fill);d.setCornerRadius(dp(c,radius));if(stroke!=0)d.setStroke(dp(c,1),stroke);return d;}
 static StateListDrawable focus(Context c){StateListDrawable d=new StateListDrawable();int[][] states={{android.R.attr.state_pressed},{android.R.attr.state_focused},{android.R.attr.state_selected}};for(int[] state:states)d.addState(state,shape(c,0xff30465f,0xffbcd8f5,12));d.addState(new int[]{},shape(c,0x00000000,0,12));return d;}
 static class Builder extends AlertDialog.Builder {
  final Context context;
  Builder(Context c){super(c);context=c;}
  @Override public Builder setTitle(CharSequence title){TextView t=new TextView(context);t.setText(title);t.setTextSize(23);t.setTextColor(0xffedf2f8);t.setTypeface(Typeface.create("sans-serif-medium",0));t.setPadding(dp(context,26),dp(context,22),dp(context,26),dp(context,14));super.setCustomTitle(t);return this;}
  @Override public Builder setItems(CharSequence[] items,DialogInterface.OnClickListener listener){
   ArrayAdapter<CharSequence> adapter=new ArrayAdapter<CharSequence>(context,android.R.layout.simple_list_item_1,items){
    public View getView(int position,View old,ViewGroup parent){TextView t=(TextView)super.getView(position,old,parent);t.setTextSize(18);t.setTextColor(0xffe1e8f1);t.setTypeface(Typeface.create("sans-serif",0));t.setGravity(Gravity.CENTER_VERTICAL);t.setMinHeight(dp(context,46));t.setSingleLine(false);t.setPadding(dp(context,18),dp(context,10),dp(context,18),dp(context,10));return t;}
   };super.setAdapter(adapter,listener);return this;
  }
  @Override public AlertDialog create(){AlertDialog dialog=super.create();dialog.setOnShowListener(d->decorate(dialog));return dialog;}
 }
 static void decorate(AlertDialog d){Context c=d.getContext();Window w=d.getWindow();if(w==null)return;
  w.setBackgroundDrawable(shape(c,0xff182330,0xff394b60,20));WindowManager.LayoutParams a=w.getAttributes();a.dimAmount=.65f;a.width=Math.min(dp(c,520),(int)(c.getResources().getDisplayMetrics().widthPixels*.82));w.setAttributes(a);w.addFlags(WindowManager.LayoutParams.FLAG_DIM_BEHIND);
  TextView message=d.findViewById(android.R.id.message);if(message!=null){message.setTextColor(0xffcbd6e3);message.setTextSize(19);message.setLineSpacing(dp(c,4),1);}
  for(int id:new int[]{DialogInterface.BUTTON_POSITIVE,DialogInterface.BUTTON_NEGATIVE,DialogInterface.BUTTON_NEUTRAL}){Button b=d.getButton(id);if(b!=null){b.setAllCaps(false);b.setTextSize(18);b.setTextColor(0xffdfebf8);b.setBackground(focus(c));b.setPadding(dp(c,20),dp(c,8),dp(c,20),dp(c,8));}}
  ListView list=d.getListView();if(list!=null){list.setDivider(null);list.setPadding(dp(c,12),dp(c,4),dp(c,12),dp(c,12));list.setClipToPadding(false);list.setSelector(focus(c));list.setDrawSelectorOnTop(false);list.requestFocus();int selected=list.getCheckedItemPosition();list.setSelection(selected>=0?selected:0);}
 }
}
