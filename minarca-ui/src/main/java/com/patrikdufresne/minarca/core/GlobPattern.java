package com.patrikdufresne.minarca.core;

import java.io.File;
import java.io.IOException;

import org.jsoup.helper.Validate;

/**
 * Instance of this class represent a globbing pattern for include or exclude.
 * 
 * @author ikus060-vm
 * @see http://www.nongnu.org/rdiff-backup/rdiff-backup.1.html
 */
public class GlobPattern {
	/**
	 * The pattern.
	 */
	private final String pattern;

	public static boolean isGlobbing(String pattern) {
		return pattern.contains("*") || pattern.contains("?");
	}

	/**
	 * Create a new glob pattern from a string. This is the default constructor.
	 * 
	 * @param pattern
	 *            the pattern
	 */
	public GlobPattern(String pattern) {
		Validate.notEmpty(pattern);
		if (!isGlobbing()) {
			// If not a globbing pattern, it should be a real file or directory.
			// Try to get the absolute location of the file.
			File f = new File(pattern);
			if (f.exists()) {
				try {
					pattern = f.getCanonicalPath();
				} catch (IOException e) {
					// Swallow exception. Keep original pattern.
				}
			}
		}
		// rdiffweb for windows doesn't support \\ separator, replace them.
		this.pattern = pattern.replace("\\", "/");
	}

	/**
	 * True if the pattern contains any globbing character to be expended.
	 * 
	 * @return
	 */
	public boolean isGlobbing() {
		return isGlobbing(this.pattern);
	}

	@Override
	public String toString() {
		return this.pattern;
	}

}
