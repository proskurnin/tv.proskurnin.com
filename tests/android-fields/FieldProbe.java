package local.proskurnin.fieldprobe;
import android.app.Activity;import android.os.Bundle;import android.widget.*;import android.text.InputType;
public class FieldProbe extends Activity {
 public void onCreate(Bundle state){super.onCreate(state);LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(100,60,100,60);setContentView(root);
 for(int i=0;i<3;i++){EditText field=new EditText(this);field.setId(100+i);field.setHint(i==2?"Password probe":"Field "+i);field.setSingleLine(true);field.setText(i==2?"TEST_PASSWORD_SENTINEL":"Field "+i);if(i==2)field.setInputType(InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);root.addView(field,new LinearLayout.LayoutParams(-1,120));}root.getChildAt(0).requestFocus();getWindow().setSoftInputMode(3);}
}
