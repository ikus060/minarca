package com.patrikdufresne.minarca.core;

import java.io.IOException;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Date;
import java.util.List;
import java.util.Locale;

import org.apache.commons.lang3.Validate;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import com.patrikdufresne.minarca.core.model.CurrentUser;
import com.patrikdufresne.minarca.core.model.MinarcaInfo;

/**
 * Client to access rdiffweb remotely.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Client {

    private static final String PREFS_SSHKEYS = "/prefs/sshkeys/";

    private static Element selectFirst(Element e, String query) {
        Elements list = e.select(query);
        if (list.size() > 0) {
            return list.get(0);
        }
        return null;
    }

    private static String selectFirstAsString(Element e, String query) {
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
     * Keep reference to web target to avoid re-login everytime.
     */
    private Requests requests;

    /**
     * Create a new rdiffweb client.
     * 
     * @param url
     */
    public Client(String url, String username, String password) {
        Validate.notEmpty(url);
        Validate.notEmpty(username);
        Validate.notEmpty(password);
        boolean ignoreSsl = Boolean.getBoolean("minarca.accepthostkey");
        this.requests = new Requests(url, ignoreSsl, Locale.getDefault()).auth(username, password);
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
        this.requests.target(PREFS_SSHKEYS).entityParam("action", "add").entityParam("title", title).entityParam("key", key).post();
    }

    /**
     * Check if authentication and connectivity is working.
     * <p>
     * Get proof of authentication. We query the api URL because it's less CPU intensive on the server.
     * 
     * @throws IllegalStateException
     *             if content stream cannot be created.
     * @throws IOException
     *             if the stream could not be created
     */
    public void check() throws IllegalStateException, IOException {
        this.requests.target("/api/currentuser/").get();
    }

    /**
     * Delete a SSH key.
     * 
     * @param keyid
     *            the key ID.
     * @throws IOException
     */
    public void deleteSSHKey(String keyid) throws IOException {
        this.requests.target(PREFS_SSHKEYS).entityParam("action", "delete").entityParam("key", keyid).post();
    }

    /**
     * Return the current user info.
     * 
     * @return current user info
     * @throws IllegalStateException
     *             if content stream cannot be created.
     * @throws IOException
     *             if the stream could not be created
     */
    public CurrentUser getCurrentUserInfo() throws IllegalStateException, IOException {
        return this.requests.target("/api/currentuser/").json(CurrentUser.class);
    }

    /**
     * Return the Minarca info
     * 
     * @return minarca info.
     * @throws IllegalStateException
     *             if content stream cannot be created.
     * @throws IOException
     *             if the stream could not be created
     */
    public MinarcaInfo getMinarcaInfo() throws IllegalStateException, IOException {
        return this.requests.target("/api/minarca/").json(MinarcaInfo.class);
    }

    /**
     * Return the URL used by this client to establish connection.
     * 
     * @return
     */
    public String getRemoteUrl() {
        return this.requests.getUrl();
    }

    /**
     * List SSH Keys.
     * 
     * @return list of keys.
     * @throws IOException
     */
    public Collection<SSHKey> getSSHKeys() throws IOException {
        // Query plugins page.
        String data = this.requests.target(PREFS_SSHKEYS).text();
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
     * Set a new repository encoding.
     * 
     * @param encoding
     *            the new encoding.
     * @throws IOException
     */
    public void setRepoEncoding(String name, String encoding) throws IOException {
        // Create query to update encding.
        this.requests.target("/api/set-encoding/" + name + "/").entityParam("new_encoding", encoding).postAsString();
    }

    /**
     * Refresh the list of repositories for the given user.
     * 
     * @throws IOException
     */
    public void updateRepositories() throws IOException {
        this.requests.target("/prefs/general/").entityParam("action", "update_repos").postAsString();
    }

}
