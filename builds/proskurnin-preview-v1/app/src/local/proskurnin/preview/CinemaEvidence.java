package local.proskurnin.preview;
/** A catalog offer and a navigable movie card are independent facts. */
final class CinemaEvidence {
 static String status(String nativeState,String webState,boolean card){if(card)return "Карточка найдена";if(nativeState.equals("pending")||webState.equals("searching")||webState.equals("pending"))return "Ищем карточку…";if(nativeState.equals("timeout")||nativeState.equals("busy"))return "Приложение не ответило";if(nativeState.equals("restricted"))return "Поиск приложения закрыт";if(nativeState.equals("error")||webState.equals("error"))return "Не удалось проверить";return "Точное совпадение не найдено";}
 static String access(String offer){return offer.isEmpty()?"Просмотр не подтверждён":"По каталогу: "+offer;}
}
