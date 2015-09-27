package com.patrikdufresne.rdiffweb.core;

import java.io.IOException;
import java.util.Date;

import org.apache.commons.lang3.Validate;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;

/**
 * Represent information related to a single repository.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Repository {

    private Client client;

    private Date lastBackup;

    private String name;

    Repository(Client client) {
        Validate.notNull(this.client = client);
    }

    /**
     * Set a new repository encoding.
     * 
     * @param encoding
     *            the new encoding.
     * @throws IOException
     */
    public void setEncoding(String encoding) throws IOException {
        // Create query to update encding.
        this.client.target("/settings/" + name + "/").entityParam("encoding", encoding).entityParam("action", "set_encoding").postAsString();
    }

    /**
     * Query the repository settings for the encoding used by this repository.
     * 
     * @return the encoding.
     * @throws IOException
     * @throws IllegalStateException
     */
    public String getEncoding() throws IllegalStateException, IOException {
        String data = this.client.target("/settings/" + name + "/").getAsString();
        // Select encoding field.
        Document doc = Jsoup.parse(data);
        Element e = Client.selectFirst(doc, "select[id=encoding] > option[selected]");
        if (e == null) {
            return null;
        }
        // String to charset
        return e.text();
    }

    /**
     * Return the last backup date.
     * 
     * @return
     */
    public Date getLastBackup() {
        return lastBackup;
    }

    /**
     * Return the name of the repository.
     * 
     * @return
     */
    public String getName() {
        return name;
    }

    void setLastBackup(Date lastBackup) {
        this.lastBackup = lastBackup;
    }

    void setName(String name) {
        this.name = name;
    }

}
