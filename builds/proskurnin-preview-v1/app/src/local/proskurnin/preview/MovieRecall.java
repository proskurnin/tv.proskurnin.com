package local.proskurnin.preview;
import java.util.Locale;
final class MovieRecall {
 static boolean requested(String query){String q=query.toLowerCase(new Locale("ru")).replaceAll("\\bне\\s+(?:смотрел[аи]?|видел[аи]?|просмотрен\\w*)\\b","");return q.matches("(?s).*\\b(?:смотрел[аи]?|видел[аи]?|пересмотреть|вспомнить|watched|rewatch)\\b.*")||q.matches("(?s).*забыл[аи]?.*(?:название|фильм).* ".trim());}
}
