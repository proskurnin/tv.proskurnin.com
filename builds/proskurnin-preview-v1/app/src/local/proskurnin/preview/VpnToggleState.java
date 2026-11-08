package local.proskurnin.preview;
final class VpnToggleState {
 boolean pending,target;long deadline;
 boolean begin(boolean connected,long now){if(pending)return false;target=!connected;pending=true;deadline=now+20000;return true;}
 // 0 waiting/idle, 1 confirmed by Android, -1 timed out. No optimistic state change.
 int poll(boolean connected,boolean known,long now){if(!pending)return 0;if(known&&connected==target){pending=false;return 1;}if(now>=deadline){pending=false;return -1;}return 0;}
 void cancel(){pending=false;}
}
