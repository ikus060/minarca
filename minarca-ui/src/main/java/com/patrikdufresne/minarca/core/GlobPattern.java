package com.patrikdufresne.minarca.core;

import java.io.File;
import java.io.IOException;
import java.nio.file.FileSystems;
import java.nio.file.Path;
import java.nio.file.PathMatcher;
import java.nio.file.Paths;

import org.jsoup.helper.Validate;

import ch.qos.logback.core.joran.spi.Pattern;

/**
 * Instance of this class represent a globbing pattern for include or exclude.
 * 
 * @author ikus060-vm
 * @see http://www.nongnu.org/rdiff-backup/rdiff-backup.1.html
 */
public class GlobPattern {
	public static boolean isGlobbing(String pattern) {
		return pattern.contains("*") || pattern.contains("?");
	}

	/**
	 * The pattern.
	 */
	private final String pattern;
	private PathMatcher matcher;

	/**
	 * Create a new glob pattern from a string. This is the default constructor.
	 * 
	 * @param pattern
	 *            the pattern
	 */
	public GlobPattern(String pattern) {
		Validate.notEmpty(pattern);
		if (!isGlobbing(pattern)) {
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
		this.pattern = encode(pattern);
	}

	public GlobPattern(File file) {
		this(getPath(file));
	}

	private static String getPath(File file) {
		try {
			return file.getCanonicalPath();
		} catch (IOException e) {
			return file.getAbsolutePath();
		}
	}

	private static String encode(String pattern) {
		return pattern.replace("\\", "/");
	}

	@Override
	public boolean equals(Object obj) {
		if (this == obj)
			return true;
		if (obj == null)
			return false;
		if (getClass() != obj.getClass())
			return false;
		GlobPattern other = (GlobPattern) obj;
		if (pattern == null) {
			if (other.pattern != null)
				return false;
		} else if (!pattern.equals(other.pattern))
			return false;
		return true;
	}

	@Override
	public int hashCode() {
		final int prime = 31;
		int result = 1;
		result = prime * result + ((pattern == null) ? 0 : pattern.hashCode());
		return result;
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
		return this.pattern.replace("/", "\\");
	}

	public String value() {
		return this.pattern;
	}

	/**
	 * Check if the given pattern matches the given filename.
	 * 
	 * @param file
	 * @return
	 */
	public boolean matches(File file) {
		// Try to get canonical name.
		String path;
		try {
			path = file.getCanonicalPath();
		} catch (IOException e) {
			path = file.getAbsolutePath();
		}
		if (isGlobbing()) {
			return matcher().matches(Paths.get(path));
		}
		return encode(path).startsWith(this.pattern);

	}

	private PathMatcher matcher() {
		if (this.matcher != null) {
			return this.matcher;
		}
		return this.matcher = FileSystems.getDefault().getPathMatcher(
				"glob:" + this.pattern);
	}
}
