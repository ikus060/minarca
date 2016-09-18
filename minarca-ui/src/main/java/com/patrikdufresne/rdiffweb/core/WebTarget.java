package com.patrikdufresne.rdiffweb.core;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;

import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.NameValuePair;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.HttpClient;
import org.apache.http.client.config.CookieSpecs;
import org.apache.http.client.config.RequestConfig;
import org.apache.http.client.entity.UrlEncodedFormEntity;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.utils.URLEncodedUtils;
import org.apache.http.entity.BufferedHttpEntity;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.message.BasicNameValuePair;
import org.jsoup.Jsoup;
import org.apache.commons.lang3.Validate;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WebTarget implements Cloneable {

    protected static final Logger LOGGER = LoggerFactory.getLogger(WebTarget.class);

    protected static final String LOGIN = "/login/";

    /**
     * Check if the page return any error.
     * 
     * @throws IOException
     */
    private static void checkPage(HttpResponse response) throws IOException {
        // Check error
        if (response == null) {
            return;
        }
        String page = toString(response);
        Document doc = Jsoup.parse(page);
        Elements elements = doc.getElementsByAttributeValueContaining("class", "alert-danger");
        if (elements.size() > 0) {
            throw new RdiffwebException(elements.get(0).html(), response);
        }
        if (page.contains("<title>Error</title>")) {
            throw new RdiffwebException("unknown!?", response);
        }
        if (page.contains("Invalid username or password.")) {
            throw new RdiffwebException("Invalid username or password.", response);
        }
    }

    /**
     * Convert the http content response to String.
     * 
     * @param response
     * @throws IOException
     * @throws IllegalStateException
     */
    public static String toString(HttpResponse response) throws IllegalStateException, IOException {
        // Replace the original entity by a buffered entity.
        HttpEntity entity = response.getEntity();
        response.setEntity(new BufferedHttpEntity(entity));

        BufferedReader rd = new BufferedReader(new InputStreamReader(response.getEntity().getContent()));

        StringBuffer result = new StringBuffer();
        String line = "";
        while ((line = rd.readLine()) != null) {
            result.append(line);
        }

        return result.toString();
    }

    /**
     * The base URL. e.g.: http:///my.domain.com/
     */
    private final String baseurl;

    /**
     * True to close http client.
     */
    private boolean close;

    private HttpEntity entity;
    /**
     * Store the HTTP header.
     */
    private final Map<String, String> headers = new LinkedHashMap<String, String>();

    /**
     * Reference to http client.
     */
    private HttpClient httpclient;

    /**
     * Store the params.
     */
    private final Map<String, String> params = new LinkedHashMap<String, String>();

    /**
     * The password.
     */
    private String password;

    /**
     * The target url.
     */
    private String target;

    /**
     * The username.
     */
    private String username;

    public WebTarget(HttpClient httpclient, String baseurl) {
        Validate.notEmpty(this.baseurl = baseurl);
        // Initialize an http client.
        if (httpclient != null) {
            this.httpclient = httpclient;
            this.close = false;
            return;
        } else {
            this.close = true;
            RequestConfig globalConfig = RequestConfig.custom().setCookieSpec(CookieSpecs.STANDARD).build();
            this.httpclient = httpclient = HttpClients.custom().setDefaultRequestConfig(globalConfig).build();
        }

    }

    public WebTarget(String baseurl) {
        Validate.notEmpty(this.baseurl = baseurl);
        // Initialize an http client.
        this.httpclient = HttpClients.createDefault();
    }

    public WebTarget clone() throws CloneNotSupportedException {
        return (WebTarget) super.clone();
    }

    /**
     * Close HTTP client. Release resources.
     */
    public void close() {
        if (close && this.httpclient instanceof CloseableHttpClient) {
            try {
                ((CloseableHttpClient) this.httpclient).close();
            } catch (IOException e) {
                // Swallow
            }
        }
        this.httpclient = null;
    }

    /**
     * Sets the http post entity.
     * 
     * @return
     */
    public WebTarget entity(HttpEntity entity) {
        this.entity = entity;
        return this;
    }

    public WebTarget entity(List<NameValuePair> namedValuePair) {
        try {
            this.entity = new UrlEncodedFormEntity(namedValuePair, "UTF-8");
        } catch (UnsupportedEncodingException e) {
            throw new IllegalStateException();
        }
        return this;
    }

    public WebTarget entityParam(String key, String value) throws IOException {
        List<NameValuePair> list = new ArrayList<NameValuePair>();
        // If already define, get current list from entity.
        if (this.entity instanceof UrlEncodedFormEntity) {
            list = URLEncodedUtils.parse(this.entity);
        }
        // Add item to list.
        list.add(new BasicNameValuePair(key, value));
        // Sets the entity again.
        try {
            this.entity = new UrlEncodedFormEntity(list, "UTF-8");
        } catch (UnsupportedEncodingException e) {
            throw new IllegalStateException();
        }
        return this;
    }

    public WebTarget formCredentials(String username, String password) {
        this.username = username;
        this.password = password;
        return this;
    }

    /**
     * Execute the HTTP request.
     * 
     * @return
     * @throws IOException
     */
    public HttpResponse get() throws IOException {
        HttpResponse response = httpGet();
        // FIXME use return code.
        String page;
        if (this.username != null && this.password != null && (page = toString(response)).contains("id=\"form-login\"")) {
            WebTarget request = new WebTarget(this.httpclient, this.baseurl)
                    .target(LOGIN)
                    .entity(getLoginFormParams(page, username, password))
                    .headers(getHeaders());
            response = request.httpPost();
            page = toString(response);
        }
        checkPage(response);
        return response;
    }

    /**
     * Execute the HTTP GET request and convert the response as string.
     * 
     * @return the response as string.
     * @throws IOException
     * @throws IllegalStateException
     */
    public String getAsString() throws IllegalStateException, IOException {
        return toString(get());
    }

    private List<NameValuePair> getFormParams(String html, String formid, Map<String, String> replacefields) throws UnsupportedEncodingException {

        Document doc = Jsoup.parse(html);

        // Google form id
        Elements inputElements;
        if (formid != null) {
            Element loginform = doc.getElementById(formid);
            inputElements = loginform.getElementsByTag("input");
        } else {
            inputElements = doc.getElementsByTag("input");
        }

        List<NameValuePair> paramList = new ArrayList<NameValuePair>();

        for (Element inputElement : inputElements) {
            String key = inputElement.attr("name");
            String value = inputElement.attr("value");

            if (replacefields.containsKey(key)) {
                value = replacefields.get(key);
            }

            paramList.add(new BasicNameValuePair(key, value));

        }

        return paramList;
    }

    /**
     * Returh the headers.
     * 
     * @return
     */
    public Map<String, String> getHeaders() {
        return Collections.unmodifiableMap(this.headers);
    }

    private List<NameValuePair> getLoginFormParams(String html, String username, String password) throws UnsupportedEncodingException {
        Map<String, String> table = new Hashtable<String, String>();
        table.put("login", username);
        table.put("password", password);
        return getFormParams(html, null, table);
    }

    /**
     * Return the resulting URL.
     * 
     * @return
     */
    public String getUrl() {

        StringBuilder buf = new StringBuilder();
        buf.append(this.baseurl.endsWith("/") ? this.baseurl.substring(0, this.baseurl.length() - 1) : this.baseurl);
        buf.append("/");
        buf.append(this.target.startsWith("/") ? this.target.substring(1, this.target.length()) : this.target);

        // Add params.
        if (this.params.size() > 0) {
            buf.append("?");
            Iterator<Entry<String, String>> iter = this.params.entrySet().iterator();
            while (iter.hasNext()) {
                Entry<String, String> e = iter.next();
                buf.append(e.getKey());
                buf.append("=");
                buf.append(e.getValue());
                if (iter.hasNext()) {
                    buf.append("&");
                }
            }
        }

        return buf.toString();
    }

    /**
     * Used to define form data (for HTTP POST).
     * 
     * @param key
     *            the param key
     * @param value
     *            the param value
     */
    public WebTarget header(String key, String value) {
        Validate.notEmpty(key);
        Validate.notEmpty(value);
        headers.put(key, value);
        return this;
    }

    /**
     * Add the given headers.
     * 
     * @param headers
     * @return
     */
    public WebTarget headers(Map<String, String> headers) {
        this.headers.putAll(headers);
        return this;
    }

    /**
     * Execute the real HTTP GET.
     * 
     * @throws IOException
     * @throws ClientProtocolException
     */
    private HttpResponse httpGet() throws ClientProtocolException, IOException {

        // Build the HTTP request.
        HttpGet request = new HttpGet(this.getUrl());
        // request.setHeader("User-Agent", USER_AGENT);
        // request.setHeader("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
        if (!headers.containsKey("Accept-Language")) {
            request.setHeader("Accept-Language", "en-US,en;q=0.5");
        }
        for (Entry<String, String> e : headers.entrySet()) {
            request.setHeader(e.getKey(), e.getValue());
        }

        // Execute the request.
        HttpResponse response = httpclient.execute(request);
        int responseCode = response.getStatusLine().getStatusCode();

        LOGGER.info("Sending 'GET' request to URL: {}", this.getUrl());
        LOGGER.info("Response Code: {}", responseCode);

        if (responseCode != 200) {
            throw new ServerException(response.toString());
        }

        return response;
    }

    private HttpResponse httpPost() throws ClientProtocolException, IOException {

        // Generate post request.
        HttpPost request = new HttpPost(this.getUrl());
        // request.setHeader("User-Agent", USER_AGENT);
        // request.setHeader("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
        if (!headers.containsKey("Accept-Language")) {
            request.setHeader("Accept-Language", "en-US,en;q=0.5");
        }
        // request.setHeader("Connection", "keep-alive");
        // request.setHeader("Referer", this.getUrl());
        // request.setHeader("Content-Type", "application/x-www-form-urlencoded");
        for (Entry<String, String> e : headers.entrySet()) {
            request.setHeader(e.getKey(), e.getValue());
        }

        Validate.notNull(this.entity);
        request.setEntity(this.entity);

        // Execute the request.
        HttpResponse response = httpclient.execute(request);
        int responseCode = response.getStatusLine().getStatusCode();

        LOGGER.info("Sending 'POST' request to URL: {}", this.getUrl());
        LOGGER.info("Post parameters: {}", this.entity);
        LOGGER.info("Response Code: {}", responseCode);

        if (responseCode != 200) {
            throw new ServerException(response.toString());
        }

        return response;

    }

    /**
     * Used to define <code>arg=key</code> in url.
     * 
     * @param key
     *            the param key
     * @param value
     *            the param value
     */
    public WebTarget param(String key, String value) {
        Validate.notEmpty(key);
        Validate.notEmpty(value);
        params.put(key, value);
        return this;
    }

    /**
     * Execute post statement.
     * 
     * @return
     * @throws IOException
     */
    public HttpResponse post() throws IOException {
        HttpResponse response = httpPost();
        // Check if we need to login.
        String page;
        if (this.username != null && this.password != null && (page = toString(response)).contains("id=\"form-login\"")) {
            WebTarget request = new WebTarget(this.httpclient, this.baseurl).target(LOGIN).entity(getLoginFormParams(page, username, password));
            response = request.httpPost();
            checkPage(response);

            // Re-execute the post.
            response = httpPost();
            page = toString(response);
            if (page.contains("id=\"form-login\"")) {
                throw new IllegalStateException("should be loggin.");
            }
        }
        checkPage(response);
        return response;
    }

    /**
     * Execute the POST statement.
     * 
     * @return
     * @throws IOException
     */
    public String postAsString() throws IOException {
        return toString(post());
    }

    /**
     * Sets the target path.
     * 
     * @param target
     * @return
     */
    public WebTarget target(String target) {
        this.target = target;
        return this;
    }
}
