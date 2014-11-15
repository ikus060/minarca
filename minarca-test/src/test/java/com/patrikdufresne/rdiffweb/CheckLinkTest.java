package com.patrikdufresne.rdiffweb;

import static org.junit.Assert.fail;

import java.io.IOException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.apache.http.client.ClientProtocolException;
import org.junit.Test;

public class CheckLinkTest extends AbstractRdiffwebTest {

	/**
	 * Check a simple browse page.
	 * 
	 * @throws ClientProtocolException
	 * @throws IOException
	 */
	@Test
	public void test() throws ClientProtocolException, IOException {
		Set<String> done = new HashSet<String>();
		done.add("#");
		Map<String, String> todo = new LinkedHashMap<String, String>();
		todo.put("/status/", "/status/");

		while (!todo.isEmpty()) {
			Entry<String, String> entry = todo.entrySet().iterator().next();
			String page = entry.getKey();
			String ref = entry.getValue();
			// Query the page. In case of error. The test is failing
			String data;
			try {
				data = get(page);
			} catch (Exception e) {
				fail("can't access page [" + page + "] referenced by [" + ref
						+ "]");
				return;
			}
			done.add(page);
			todo.remove(page);

			// Get href in the page.
			Pattern p = Pattern.compile("href=\"([^\"]+)\"");
			Matcher m = p.matcher(data);
			while (m.find()) {
				String newpage = m.group(1);
				newpage = newpage.replace("&amp;", "&");
				if (newpage.startsWith("?")) {
					newpage = page.replaceAll("\\?.*", "") + newpage;
				}
				if (!done.contains(newpage) && !blacklisted(newpage)) {
					todo.put(newpage, page);
				}
			}
		}

	}

	private static boolean blacklisted(String newpage) {
		// Make to to browse only our testcases repository
		if (newpage.startsWith("/browse") && !newpage.startsWith("/browse/testcases")) {
			return true;
		}
		if (newpage.startsWith("/restore") && !newpage.startsWith("/restore/testcases")) {
			return true;
		}
		return false;
	}

}
