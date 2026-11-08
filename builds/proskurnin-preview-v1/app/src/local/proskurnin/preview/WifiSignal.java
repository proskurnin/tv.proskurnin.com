package local.proskurnin.preview;
/** Five visual levels: 0..4 lit arcs. Invalid RSSI must never look like full reception. */
final class WifiSignal {
 static int level(int rssi){if(rssi<=-127||rssi>=0)return -1;if(rssi<=-100)return 0;if(rssi>=-55)return 4;return (rssi+100)*4/45;}
 static boolean lit(int level,int arc){return level>=arc&&arc>=1&&arc<=4;}
}
