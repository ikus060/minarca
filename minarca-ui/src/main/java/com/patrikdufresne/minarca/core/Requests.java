package com.patrikdufresne.minarca.core;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.UnsupportedEncodingException;
import java.security.KeyManagementException;
import java.security.KeyStoreException;
import java.security.NoSuchAlgorithmException;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Hashtable;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Map.Entry;

import org.apache.commons.lang3.Validate;
import org.apache.http.HttpEntity;
import org.apache.http.HttpResponse;
import org.apache.http.NameValuePair;
import org.apache.http.auth.AuthScope;
import org.apache.http.auth.UsernamePasswordCredentials;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.CredentialsProvider;
import org.apache.http.client.HttpClient;
import org.apache.http.client.HttpResponseException;
import org.apache.http.client.entity.UrlEncodedFormEntity;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpPost;
import org.apache.http.client.utils.URLEncodedUtils;
import org.apache.http.conn.ssl.SSLConnectionSocketFactory;
import org.apache.http.conn.ssl.SSLContextBuilder;
import org.apache.http.conn.ssl.TrustStrategy;
import org.apache.http.entity.BufferedHttpEntity;
import org.apache.http.impl.client.BasicCredentialsProvider;
import org.apache.http.impl.client.CloseableHttpClient;
import org.apache.http.impl.client.HttpClientBuilder;
import org.apache.http.impl.client.HttpClients;
import org.apache.http.message.BasicNameValuePair;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;

public class Requests implements Cloneable {

    protected static final Gson GSON = new GsonBuilder().create();

    protected static final Logger LOGGER = LoggerFactory.getLogger(Requests.class);

    protected static final String LOGIN = "/login/";

    /**
     * Convert the HTTP content into Json document.
     * 
     * @param response
     *            the reponse to be parsed.
     * @return response parsed as Json.
     * @throws IllegalStateException
     *             if content stream cannot be created.
     * @throws IOException
     *             if the stream could not be created
     */
    public static <T> T toJson(HttpResponse response, Class<T> type) throws IllegalStateException, IOException {
        // Replace the original entity by a buffered entity.
        HttpEntity entity = response.getEntity();
        response.setEntity(new BufferedHttpEntity(entity));
        BufferedReader rd = new BufferedReader(new InputStreamReader(response.getEntity().getContent()));
        return GSON.fromJson(rd, type);
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
     * True to raise exception on alert-danger.
     */
    private boolean checkDangerException = true;

    /**
     * True to raise exception on alert-info.
     */
    private boolean checkInfoException = false;

    /**
     * True to raise exception on alert-warning.
     */
    private boolean checkWarningException = false;
    /**
     * True to close http client.
     */
    private boolean close;

    private CredentialsProvider credentialsProvider = new BasicCredentialsProvider();

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
     * Locale.
     */
    private Locale locale;

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

    /**
     * Create a new requests
     * 
     * @param httpclient
     *            the http client to be used.
     * @param baseurl
     *            the base url.
     * @param locale
     *            the locale.
     */
    public Requests(HttpClient httpclient, String baseurl, Locale locale) {
        Validate.notEmpty(this.baseurl = baseurl);
        Validate.notNull(this.locale = locale);
        Validate.notNull(this.httpclient = httpclient);
        this.close = false;
    }

    /**
     * Default constructor
     * 
     * @param baseurl
     *            the base URL
     */
    public Requests(String baseurl) {
        this(baseurl, false, Locale.getDefault());
    }

    /**
     * Create a new web target.
     * 
     * @param httpclient
     *            the HTTP client
     * @param baseurl
     *            the base URL
     * @param locale
     *            the locale
     */
    public Requests(String baseurl, boolean ignoreSsl, Locale locale) {
        Validate.notEmpty(this.baseurl = baseurl);
        Validate.notNull(this.locale = locale);
        this.close = true;
        HttpClientBuilder builder = HttpClients.custom();
        if (ignoreSsl) {
            LOGGER.info("ignore ssl validation");
            SSLContextBuilder sslBuilder = new SSLContextBuilder();
            try {
                sslBuilder.loadTrustMaterial(null, new TrustStrategy() {
                    @Override
                    public boolean isTrusted(X509Certificate[] chain, String authType) throws CertificateException {
                        return true;
                    }
                });
                SSLConnectionSocketFactory sslsf = new SSLConnectionSocketFactory(sslBuilder.build());
                builder.setSSLSocketFactory(sslsf);
            } catch (NoSuchAlgorithmException | KeyStoreException | KeyManagementException e) {
                // Usually never happen.
                LOGGER.error("error while creating http client without ssl validation", e);
            }
        }
        this.httpclient = builder.setDefaultCredentialsProvider(credentialsProvider).build();
    }

    /**
     * Default constructor
     * 
     * @param baseurl
     *            the base URL
     * @param locale
     *            the locale
     */
    public Requests(String baseurl, Locale locale) {
        this(baseurl, false, locale);
    }

    public Requests auth(String username, String password) {
        UsernamePasswordCredentials credentials = new UsernamePasswordCredentials(username, password);
        credentialsProvider.setCredentials(AuthScope.ANY, credentials);
        this.username = username;
        this.password = password;
        return this;
    }

    /**
     * Checks the page for any exception.
     * 
     * @return
     */
    public Requests checkException() {
        return checkException(false, false, true);
    }

    /**
     * Check the page for exception.
     * 
     * @param info
     *            True to raise exception on alert-info
     * @param warning
     *            True to raise exception on alert-warning
     * @param danger
     *            True to raise exception on alert-danger
     * @return Same instance for chainning.
     */
    public Requests checkException(boolean info, boolean warning, boolean danger) {
        this.checkInfoException = info;
        this.checkWarningException = warning;
        this.checkDangerException = danger;
        return this;
    }

    /**
     * Check if an exception should be thrown.
     * 
     * @throws IOException
     */
    private void checkPage(HttpResponse response) throws IOException {
        // If the response is empty, don't raise exception.
        if (response == null) {
            return;
        }
        int responseCode = response.getStatusLine().getStatusCode();
        if (responseCode >= 300) {
            throw new HttpResponseException(responseCode, response.getStatusLine().getReasonPhrase());
        }
        // Parse page to find alert.
        String page = toString(response);
        Document doc = Jsoup.parse(page);
        Elements elements = doc.getElementsByAttributeValueContaining("role", "alert");
        for (Element e : elements) {
            // Check if the alert should raise exception.
            String cls = e.attr("class");
            if (checkInfoException
                    && cls.contains("alert-info")
                    || checkWarningException
                    && cls.contains("alert-warning")
                    || checkDangerException
                    && cls.contains("alert-danger")) {
                String message = e.text();
                // Remove the "X" sign from the message.
                if (message.startsWith("\u00D7")) {
                    message = message.substring(1);
                }
                throw new RdiffwebException(message, response);
            }
        }

    }

    @Override
    public Requests clone() throws CloneNotSupportedException {
        return (Requests) super.clone();
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
    public Requests entity(HttpEntity entity) {
        this.entity = entity;
        return this;
    }

    public Requests entity(List<NameValuePair> namedValuePair) {
        try {
            this.entity = new UrlEncodedFormEntity(namedValuePair, "UTF-8");
        } catch (UnsupportedEncodingException e) {
            throw new IllegalStateException();
        }
        return this;
    }

    public Requests entityParam(String key, String value) throws IOException {
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

    /**
     * Execute the HTTP request.
     * 
     * @return
     * @throws IOException
     */
    public HttpResponse get() throws IOException {
        HttpResponse response = httpGet();

        String page;
        if (this.username != null && this.password != null && (page = toString(response)).contains("id=\"form-login\"")) {
            Requests request = new Requests(this.httpclient, this.baseurl, this.locale)
                    .target(LOGIN)
                    .checkException(false, true, true)
                    .entity(getLoginFormParams(page, username, password))
                    .headers(getHeaders());
            response = request.httpPost();
            // Check if login.
            page = toString(response);
            if (page.contains("id=\"form-login\"")) {
                request.checkPage(response);
            }
        }
        checkPage(response);
        return response;
    }

    /**
     * Return accept language for HTTP header.
     */
    private String getAcceptLanguage() {
        // en-US,en;q=0.5
        return this.locale.getLanguage() + "," + this.locale.getLanguage() + "-" + this.locale.getCountry() + ";q=0.5";
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
    public Requests header(String key, String value) {
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
    public Requests headers(Map<String, String> headers) {
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
            request.setHeader("Accept-Language", getAcceptLanguage());
        }
        for (Entry<String, String> e : headers.entrySet()) {
            request.setHeader(e.getKey(), e.getValue());
        }
        // Execute the request.
        HttpResponse response = httpclient.execute(request);
        int responseCode = response.getStatusLine().getStatusCode();

        LOGGER.info("Sending 'GET' request to URL: {}", this.getUrl());
        LOGGER.info("Response Code: {}", responseCode);

        return response;
    }

    private HttpResponse httpPost() throws ClientProtocolException, IOException {

        // Generate post request.
        HttpPost request = new HttpPost(this.getUrl());
        // request.setHeader("User-Agent", USER_AGENT);
        // request.setHeader("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
        if (!headers.containsKey("Accept-Language")) {
            request.setHeader("Accept-Language", getAcceptLanguage());
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
     * Execute the HTTP GET request and convert the response to Json.
     * 
     * @return response parsed as Json.
     * @throws IllegalStateException
     *             if content stream cannot be created.
     * @throws IOException
     *             if the stream could not be created
     */
    public JsonElement json() throws IllegalStateException, IOException {
        return toJson(get(), JsonElement.class);
    }

    /**
     * Execute the HTTP GET request and convert the response to Json.
     * 
     * @param type
     *            type of data to convert into.
     * 
     * @return response parsed as Json.
     * @throws IllegalStateException
     *             if content stream cannot be created.
     * @throws IOException
     *             if the stream could not be created
     */
    public <T> T json(Class<T> type) throws IllegalStateException, IOException {
        return toJson(get(), type);
    }

    /**
     * Used to define <code>arg=key</code> in url.
     * 
     * @param key
     *            the param key
     * @param value
     *            the param value
     */
    public Requests param(String key, String value) {
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
            Requests request = new Requests(this.httpclient, this.baseurl, this.locale)
                    .target(LOGIN)
                    .checkException(false, true, true)
                    .entity(getLoginFormParams(page, username, password));
            response = request.httpPost();
            request.checkPage(response);

            // Re-execute the post.
            response = httpPost();
            page = toString(response);
            if (page.contains("id=\"form-login\"")) {
                throw new IllegalStateException("should be logged-in");
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
    public Requests target(String target) {
        Requests r;
        try {
            r = this.clone();
        } catch (CloneNotSupportedException e) {
            throw new IllegalStateException();
        }
        r.target = target;
        return r;
    }

    /**
     * Execute the HTTP GET request and convert the response as string.
     * 
     * @return the response as string.
     * @throws IOException
     * @throws IllegalStateException
     */
    public String text() throws IllegalStateException, IOException {
        return toString(get());
    }
}
