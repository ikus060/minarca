package com.patrikdufresne.rdiffweb.core;

import java.io.IOException;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.jsoup.Jsoup;
import org.apache.commons.lang3.Validate;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

/**
 * Client to access rdiffweb remotely.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Client {

    private static final String PREFS_SSHKEYS = "/prefs/sshkeys/";

    protected static Element selectFirst(Element e, String query) {
        Elements list = e.select(query);
        if (list.size() > 0) {
            return list.get(0);
        }
        return null;
    }

    protected static Boolean selectFirstAsBoolean(Element e, String query) {
        String value = selectFirstAsString(e, query);
        if (value == null) {
            return null;
        }
        return Boolean.valueOf(value);
    }

    /**
     * Parse the given element value as date.
     * 
     * @param e
     * @param query
     * @return
     */
    protected static Date selectFirstAsDate(Element e, String query) {
        String value = selectFirstAsString(e, query);
        if (value == null) {
            return null;
        }
        // Parse the date value.
        try {
            return new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").parse(value);
        } catch (ParseException exc) {
            return null;
        }
    }

    protected static Integer selectFirstAsInt(Element e, String query) {
        String value = selectFirstAsString(e, query);
        if (value == null) {
            return null;
        }
        return Integer.valueOf(value);
    }

    protected static Long selectFirstAsLong(Element e, String query) {
        String value = selectFirstAsString(e, query);
        if (value == null) {
            return null;
        }
        return Long.valueOf(value);
    }

    protected static String selectFirstAsString(Element e, String query) {
        Element f = selectFirst(e, query);
        if (f != null) {
            String content = f.attr("content");
            if (content != null && content.length() > 0) {
                return content;
            }
            return f.text();
        }
        return null;
    }

    /**
     * The crendentials
     */
    private String password;

    /**
     * The credentials.
     */
    private String username;

    /**
     * Keep reference to web target to avoid re-login everytime.
     */
    private WebTarget target;

    /**
     * Create a new rdiffweb client.
     * 
     * @param url
     */
    public Client(String url, String username, String password) {
        Validate.notEmpty(url);
        Validate.notEmpty(this.username = username);
        Validate.notEmpty(this.password = password);
        this.target = new WebTarget(url);
    }

    /**
     * Add an SSH Key.
     * 
     * @param title
     *            an SSH title (optional)
     * @param key
     *            the key (starting with ssh-rsa...)
     * @throws IOException
     */
    public void addSSHKey(String title, String key) throws IOException {
        target(PREFS_SSHKEYS).entityParam("action", "add").entityParam("title", title).entityParam("key", key).post();
    }

    /**
     * Check if authentication and connectivity is working.
     * <p>
     * Get proof of authentication. We query the user preferences because it's the less CPU intensive page.
     * 
     * @throws IOException
     * @throws IllegalStateException
     */
    public void check() throws IllegalStateException, IOException {
        target("/prefs/general/").getAsString();
    }

    /**
     * Delete a SSH key.
     * 
     * @param keyid
     *            the key ID.
     * @throws IOException
     */
    public void deleteSSHKey(String keyid) throws IOException {
        target(PREFS_SSHKEYS).entityParam("action", "delete").entityParam("key", keyid).post();
    }

    /**
     * Return the curent version.
     * 
     * @return
     * @throws IOException
     */
    public String getCurrentVersion() throws IOException {
        // Check current version.
        String data = target("/").formCredentials(null, null).getAsString();
        Pattern p = Pattern.compile("<meta name=\"app-version\" content=\"([^\"]*)\">");
        Matcher m = p.matcher(data);
        if (m.find()) {
            return m.group(1);
        }
        return null;
    }

    /**
     * Get the plugin info for the given plugin name.
     * 
     * @param name
     * @return the plugin info or null.
     * @throws IOException
     */
    public PluginInfo getPluginInfo(String name) throws IOException {
        for (PluginInfo p : getPluginInfos()) {
            if (name.equals(p.getName())) {
                return p;
            }
        }
        return null;
    }

    /**
     * List plugins information.
     * 
     * @return list of plugin information.
     * 
     * @throws IOException
     */
    public Collection<PluginInfo> getPluginInfos() throws IOException {
        // Query plugins page.
        String data = target("/admin/plugins/").getAsString();
        // Select plugin items.
        Document doc = Jsoup.parse(data);
        Elements plugins = doc.select("[itemtype=https://schema.org/SoftwareApplication]");
        List<PluginInfo> list = new ArrayList<PluginInfo>(plugins.size());
        for (Element e : plugins) {
            String name = selectFirstAsString(e, "[itemprop=name]");
            String version = selectFirstAsString(e, "[itemprop=softwareVersion]");
            Boolean enabled = selectFirstAsBoolean(e, "[itemprop=installed]");
            String author = selectFirstAsString(e, "[itemprop=author]");
            String description = selectFirstAsString(e, "[itemprop=description]");
            // Create plugin object from properties found.
            PluginInfo p = new PluginInfo();
            p.setAuthor(author);
            p.setDescription(description);
            p.setName(name);
            p.setVersion(version);
            p.setEnabled(enabled);
            list.add(p);
        }
        return list;
    }

    /**
     * Return list of repositories.
     * 
     * @return
     */
    public Collection<Repository> getRepositories() throws IOException {
        // Query plugins page.
        String data = target("/").getAsString();
        // Select plugin items.
        Document doc = Jsoup.parse(data);
        Elements repos = doc.select("[itemtype=http://schema.org/ListItem]");
        List<Repository> list = new ArrayList<Repository>(repos.size());
        for (Element e : repos) {
            String name = selectFirstAsString(e, "[itemprop=name]");
            Date lastBackup = selectFirstAsDate(e, "[itemprop=lastBackupDate]");
            // Create plugin object from properties found.
            Repository r = new Repository(this);
            r.setName(name);
            r.setLastBackup(lastBackup);
            list.add(r);
        }
        return list;
    }

    /**
     * Get information related to specific repository.
     * 
     * @return repository info.
     * 
     * @throws IOException
     */
    public Repository getRepositoryInfo(String name) throws IOException {
        for (Repository r : getRepositories()) {
            if (name.equals(r.getName())) {
                return r;
            }
        }
        return null;
    }

    /**
     * List SSH Keys.
     * 
     * @return list of keys.
     * @throws IOException
     */
    public Collection<SSHKey> getSSHKeys() throws IOException {
        // Query plugins page.
        String data = target(PREFS_SSHKEYS).getAsString();
        // Select plugin items.
        Document doc = Jsoup.parse(data);
        Elements keys = doc.select("[itemtype=http://schema.org/ListItem]");
        List<SSHKey> list = new ArrayList<SSHKey>(keys.size());
        for (Element e : keys) {
            String id = selectFirstAsString(e, "[itemprop=id]");
            String title = selectFirstAsString(e, "[itemprop=name]");
            String fingerprint = selectFirstAsString(e, "[itemprop=fingerprint]");
            // Create plugin object from properties found.
            SSHKey p = new SSHKey();
            p.setId(id);
            p.setTitle(title);
            p.setFingerprint(fingerprint);
            list.add(p);
        }
        return list;
    }

    /**
     * Get usage information. Only available if minarca plugin is available.
     * 
     * @return return disk usage information.
     * 
     * @throws IOException
     */
    public UsageInfo getUsageInfo() throws IOException {

        // Query page.
        String data = target("/").getAsString();
        // Select plugin items.
        Document doc = Jsoup.parse(data);
        Element e = selectFirst(doc, "[itemtype=https://schema.org/Filesystem]");
        if (e == null) {
            return null;
        }
        UsageInfo info = new UsageInfo();
        info.setFree(selectFirstAsLong(e, "[itemprop=freeSpace]"));
        info.setTotal(selectFirstAsLong(e, "[itemprop=totalSpace]"));
        info.setUsed(selectFirstAsLong(e, "[itemprop=occupiedSpace]"));
        return info;

    }

    /**
     * Return the username used to authenticate.
     * 
     * @return
     */
    public String getUsername() {
        return this.username;
    }

    protected WebTarget target(String target) {
        try {
            return this.target.clone().target(target).formCredentials(username, password);
        } catch (CloneNotSupportedException e) {
            throw new RuntimeException();
        }
    }

    /**
     * Refresh the list of repositories for the given user.
     * 
     * @throws IOException
     */
    public void updateRepositories() throws IOException {
        target("/prefs/general/").entityParam("action", "update_repos").postAsString();
    }

}
