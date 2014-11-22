package com.patrikdufresne.minarca.core;

public class APIException extends Exception {

	private static final long serialVersionUID = 1L;

	/**
	 * Exception used to represent an application error. Message return in
	 * alert-danger.
	 * 
	 * @author ikus060
	 * 
	 */
	public static class ApplicationException extends APIException {
		public ApplicationException(String message) {
			super(message);
		}
	}

	/**
	 * Thrown when the application is not configured.
	 * 
	 * @author ikus060-vm
	 *
	 */
	public static class NotConfiguredException extends APIException {
		public NotConfiguredException(String message) {
			super(message);
		}
	}

	/**
	 * Thrown when the application is miss configured
	 * 
	 * @author ikus060-vm
	 *
	 */
	public static class MissConfiguredException extends APIException {
		public MissConfiguredException(String message) {
			super(message);
		}

		public MissConfiguredException(String message, Exception cause) {
			super(message, cause);
		}
	}

	public APIException(String message) {
		super(message);
	}

	public APIException(Exception cause) {
		super(cause);
	}

	public APIException(String message, Exception e) {
		super(message, e);
	}

}
