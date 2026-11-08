package local.proskurnin.preview;

import java.util.*;

/** Persisted package identities, independent of Android views and labels. */
final class AppArrangement {
    static final int LIMIT = 6;
    final ArrayList<String> home = new ArrayList<>();
    final ArrayList<String> apps = new ArrayList<>();
    final ArrayList<String> other = new ArrayList<>();

    AppArrangement copy() {
        AppArrangement result = new AppArrangement();
        result.home.addAll(home); result.apps.addAll(apps); result.other.addAll(other);
        return result;
    }

    void reconcile(Collection<String> installed) {
        HashSet<String> allowed = new HashSet<>(installed), seen = new HashSet<>();
        clean(home, allowed, seen, LIMIT);
        clean(other, allowed, seen, Integer.MAX_VALUE);
        clean(apps, allowed, seen, Integer.MAX_VALUE);
        for (String pkg : installed) if (valid(pkg) && seen.add(pkg)) apps.add(pkg);
    }

    private static void clean(ArrayList<String> list, Set<String> allowed, Set<String> seen, int limit) {
        int count = 0;
        for (Iterator<String> it = list.iterator(); it.hasNext();) {
            String pkg = it.next();
            if (!valid(pkg) || !allowed.contains(pkg) || count >= limit || !seen.add(pkg)) it.remove();
            else count++;
        }
    }
    private static boolean valid(String pkg) { return pkg != null && !pkg.isEmpty(); }

    /** Full home requires an explicit replacement slot. Existing home entries swap. */
    boolean pin(String pkg, int slot) {
        if (!valid(pkg) || !(home.contains(pkg) || apps.contains(pkg) || other.contains(pkg))) return false;
        int previous = home.indexOf(pkg);
        if (previous >= 0) {
            if (slot < 0 || slot >= home.size()) return false;
            Collections.swap(home, previous, slot); return true;
        }
        if (home.size() >= LIMIT && (slot < 0 || slot >= home.size())) return false;
        if (slot < 0) slot = home.size();
        if (slot > home.size()) return false;
        apps.remove(pkg); other.remove(pkg);
        if (slot < home.size()) apps.add(home.set(slot, pkg));
        else home.add(pkg);
        return true;
    }

    /** Null replacement deliberately reduces the favorite row, including to zero. */
    boolean hide(String pkg, String replacement) {
        int slot = home.indexOf(pkg);
        if (!(slot >= 0 || apps.contains(pkg)) || pkg.equals(replacement)) return false;
        if (replacement != null && (slot < 0 || !apps.contains(replacement))) return false;
        if (slot >= 0) {
            if (replacement == null) home.remove(slot);
            else { apps.remove(replacement); home.set(slot, replacement); }
        }
        apps.remove(pkg); other.remove(pkg); other.add(pkg); return true;
    }

    void unpin(String pkg) { if (home.remove(pkg)) apps.add(pkg); }
    void restore(String pkg) { if (other.remove(pkg)) apps.add(pkg); }

    static int move(ArrayList<String> list, int from, int to) {
        if (from < 0 || from >= list.size()) return from;
        to = Math.max(0, Math.min(to, list.size() - 1));
        if (from != to) list.add(to, list.remove(from));
        return to;
    }

    /** Same six-column reorder operation on Home, the app drawer and Other. */
    static int reorder(ArrayList<String> list, int index, int key) {
        return move(list, index, next(index, list.size(), key, LIMIT));
    }

    static int next(int index, int count, int key, int columns) {
        if (count <= 0) return 0;
        if (key == 21 && index % columns > 0) return index - 1;
        if (key == 22 && index % columns < columns - 1 && index + 1 < count) return index + 1;
        if (key == 19 && index >= columns) return index - columns;
        if (key == 20 && index / columns < (count - 1) / columns) return Math.min(index + columns, count - 1);
        return index;
    }

    static float homeLeft(int count) { return (1920f - (count * 260 + Math.max(0, count - 1) * 25)) / 2; }
}
