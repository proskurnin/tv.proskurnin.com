package local.proskurnin.preview;
import android.app.*;import android.os.*;import android.content.*;import android.content.pm.*;import android.graphics.*;import android.graphics.drawable.*;import android.view.*;import android.widget.*;import android.speech.RecognizerIntent;import java.util.*;
abstract class VoiceActivity extends Activity {
 Handler handler=new Handler();TextView status;EditText input;Button voiceButton;boolean busy=false,listening=false;volatile boolean alive=true;int speechGeneration=0;Runnable speechTimeout;android.speech.SpeechRecognizer recognizer;
 abstract void submit();
 int dp(int value){return Math.round(value*getResources().getDisplayMetrics().density);}
 TextView label(String text,int size){TextView v=new TextView(this);v.setText(text);v.setTextColor(0xffe9edf5);v.setTextSize(size);v.setFontFeatureSettings("kern");return v;}
 GradientDrawable panel(int color,int stroke){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(12));if(stroke!=0)d.setStroke(dp(1),stroke);return d;}
 android.graphics.drawable.StateListDrawable focusBackground(){StateListDrawable d=new StateListDrawable();d.addState(new int[]{android.R.attr.state_focused},panel(0xff344863,0xffc5dcff));d.addState(new int[]{},panel(0xff192332,0));return d;}
 Button button(String title){Button b=new Button(this);b.setId(View.generateViewId());b.setText(title);b.setTextSize(16);b.setAllCaps(false);b.setTextColor(0xffe9edf5);b.setBackground(focusBackground());b.setPadding(dp(14),0,dp(14),0);b.setMinHeight(0);b.setMinimumHeight(0);b.setMinWidth(0);b.setMinimumWidth(0);return b;}
 LinearLayout base(String title,String eyebrow){getWindow().setBackgroundDrawable(new ColorDrawable(0xff0c121c));getWindow().getDecorView().setSystemUiVisibility(5894);getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_HIDDEN);LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(36),dp(22),dp(36),dp(20));root.setBackgroundColor(0xff0c121c);setContentView(root);TextView tag=label(eyebrow,12);tag.setTextColor(0xff9eafc7);tag.setLetterSpacing(.15f);root.addView(tag);TextView heading=label(title,32);heading.setTypeface(Typeface.create("sans-serif-light",0));LinearLayout.LayoutParams hp=new LinearLayout.LayoutParams(-1,dp(56));hp.bottomMargin=dp(10);root.addView(heading,hp);return root;}
 void addInput(LinearLayout root,String hint){input=new EditText(this);input.setId(View.generateViewId());input.setSingleLine(true);input.setTextSize(18);input.setTextColor(Color.WHITE);input.setHintTextColor(0xff8796ac);input.setHint(hint);input.setBackground(focusBackground());input.setPadding(dp(18),0,dp(18),0);input.setImeOptions(android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH);root.addView(input,new LinearLayout.LayoutParams(-1,dp(48)));input.setOnEditorActionListener((v,action,event)->{if(action==android.view.inputmethod.EditorInfo.IME_ACTION_SEARCH){((android.view.inputmethod.InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(input.getWindowToken(),0);submit();return true;}return false;});}
 void addActions(LinearLayout root,Button... buttons){
  LinearLayout row=new LinearLayout(this);LinearLayout.LayoutParams rp=new LinearLayout.LayoutParams(-1,dp(32));rp.topMargin=dp(10);rp.bottomMargin=dp(5);root.addView(row,rp);
  for(int i=0;i<buttons.length;i++){Button b=buttons[i];b.setTextSize(13);b.setPadding(dp(7),0,dp(7),0);b.setSingleLine(true);b.setHorizontallyScrolling(false);b.setAutoSizeTextTypeUniformWithConfiguration(10,13,1,android.util.TypedValue.COMPLEX_UNIT_SP);
   LinearLayout.LayoutParams bp=buttons.length>6?new LinearLayout.LayoutParams(0,-1,1):new LinearLayout.LayoutParams(dp(106),-1);if(i<buttons.length-1)bp.rightMargin=dp(6);row.addView(b,bp);
   b.setNextFocusUpId(input.getId());b.setNextFocusLeftId(i>0?buttons[i-1].getId():b.getId());b.setNextFocusRightId(i+1<buttons.length?buttons[i+1].getId():b.getId());
  }
  input.setNextFocusDownId(buttons[0].getId());input.setOnKeyListener((v,key,event)->{if(key==KeyEvent.KEYCODE_DPAD_DOWN){if(event.getAction()==KeyEvent.ACTION_DOWN)buttons[0].requestFocus();return true;}return false;});status=label("",14);status.setTextColor(0xffa9b8cd);status.setMaxLines(2);status.setPadding(0,dp(4),0,dp(6));root.addView(status,new LinearLayout.LayoutParams(-1,dp(43)));
 }
 void toggleStyle(Button button,boolean enabled){
  StateListDrawable d=new StateListDrawable();int base=enabled?0xff20352d:0xff39282d;
  d.addState(new int[]{android.R.attr.state_focused},panel(enabled?0xff314e40:0xff523940,enabled?0xffbfdcc9:0xffdec0c5));d.addState(new int[]{},panel(base,0));button.setBackground(d);button.setTextColor(enabled?0xffb4d6be:0xffdbb6bc);
 }
 protected void onResume(){super.onResume();phoneQuery();if(getIntent().getBooleanExtra("auto_voice",false)){getIntent().removeExtra("auto_voice");handler.postDelayed(()->{if(alive&&hasWindowFocus())voice();},450);}}
 protected void onNewIntent(Intent intent){super.onNewIntent(intent);setIntent(intent);phoneQuery();if(intent.getBooleanExtra("auto_voice",false)){intent.removeExtra("auto_voice");if(listening)stopVoice();handler.postDelayed(()->{if(alive&&hasWindowFocus())voice();},250);}}
 void phoneQuery(){String text=getIntent().getStringExtra("phone_query");if(text==null)return;getIntent().removeExtra("phone_query");if(text.trim().length()<2||text.length()>512)return;handler.post(()->{if(alive&&!busy){if(listening)stopVoice();input.setText(text);submit();}});}
 void voice(){
  if(listening){stopVoice();status.setText("Голосовой ввод отменён");return;}
  if(busy){status.setText("Дождитесь завершения подбора");return;}
  if(!android.speech.SpeechRecognizer.isRecognitionAvailable(this)){status.setText("Нет службы распознавания речи. Доступен ввод текста.");return;}
  if(checkSelfPermission(android.Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{android.Manifest.permission.RECORD_AUDIO},502);return;}
  final int session=++speechGeneration;listening=true;voiceButton.setText("Стоп голос");status.setText("Подключаем микрофон…");
  try{
   recognizer=android.speech.SpeechRecognizer.createSpeechRecognizer(this);
   recognizer.setRecognitionListener(new android.speech.RecognitionListener(){
    boolean current(){return alive&&listening&&session==speechGeneration;}
    public void onReadyForSpeech(Bundle p){if(current())status.setText("Говорите в микрофон пульта · Back — отмена");}
    public void onBeginningOfSpeech(){if(current())status.setText("Слушаю…");}
    public void onRmsChanged(float rms){}public void onBufferReceived(byte[] b){}
    public void onEndOfSpeech(){if(current())status.setText("Распознаю фразу…");}
    public void onError(int error){if(!current())return;stopVoice();android.util.Log.i("ProskurninVoice","error="+error);if(!retryVoice(error))status.setText(voiceError(error));}
    public void onResults(Bundle results){if(!current())return;ArrayList<String> phrases=results==null?null:results.getStringArrayList(android.speech.SpeechRecognizer.RESULTS_RECOGNITION);stopVoice();boolean valid=phrases!=null&&!phrases.isEmpty()&&phrases.get(0)!=null&&!phrases.get(0).trim().isEmpty();android.util.Log.i("ProskurninVoice","result="+(valid?"received":"empty"));if(valid){input.setText(phrases.get(0).trim());submit();}else if(!retryVoice(7))status.setText("Речь не распознана. Нажмите «Голос» и повторите.");}
    public void onPartialResults(Bundle results){if(!current()||results==null)return;ArrayList<String> phrases=results.getStringArrayList(android.speech.SpeechRecognizer.RESULTS_RECOGNITION);if(phrases!=null&&!phrases.isEmpty())status.setText("Слышу: «"+phrases.get(0)+"»");}
    public void onEvent(int type,Bundle params){}
   });
   Intent intent=new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL,RecognizerIntent.LANGUAGE_MODEL_FREE_FORM).putExtra(RecognizerIntent.EXTRA_LANGUAGE,"ru-RU").putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS,true).putExtra(RecognizerIntent.EXTRA_MAX_RESULTS,1);
   speechTimeout=()->{if(session==speechGeneration&&listening){stopVoice();if(retryVoice(6))return;status.setText("Распознавание заняло слишком долго. Проверьте сеть и повторите.");}};handler.postDelayed(speechTimeout,25000);recognizer.startListening(intent);
  }catch(Exception e){stopVoice();status.setText("Не удалось запустить микрофон. Проверьте разрешение и службу распознавания.");}
 }
 boolean retryVoice(int error){return false;}
 String voiceError(int error){switch(error){case 1:case 2:return "Распознаватель недоступен по сети. Повторите позже или введите текст.";case 3:return "Нет звука с микрофона. Проверьте подключение пульта.";case 6:case 7:return "Речь не распознана. Нажмите «Голос» и повторите.";case 8:return "Микрофон занят. Закройте другой голосовой поиск и повторите.";case 9:return "Разрешите доступ к микрофону в настройках приложения.";default:return "Ошибка распознавания ("+error+"). Нажмите «Голос» для повтора.";}}
 void stopVoice(){listening=false;speechGeneration++;if(speechTimeout!=null){handler.removeCallbacks(speechTimeout);speechTimeout=null;}if(recognizer!=null){android.speech.SpeechRecognizer old=recognizer;recognizer=null;try{old.cancel();}catch(Exception ignored){}try{old.destroy();}catch(Exception ignored){}}if(voiceButton!=null)voiceButton.setText("Голос");}
 public void onRequestPermissionsResult(int request,String[] permissions,int[] grants){super.onRequestPermissionsResult(request,permissions,grants);if(request==502)status.setText(grants.length>0&&grants[0]==PackageManager.PERMISSION_GRANTED?"Микрофон разрешён. Нажмите «Голос», когда будете готовы.":"Микрофон не разрешён. Доступен ввод текста.");}

 public void onBackPressed(){if(listening){stopVoice();status.setText("Голосовой ввод отменён");return;}super.onBackPressed();}
 protected void onPause(){if(listening){stopVoice();status.setText("Голосовой ввод остановлен");}super.onPause();}
 protected void onDestroy(){alive=false;stopVoice();handler.removeCallbacksAndMessages(null);super.onDestroy();}
}
