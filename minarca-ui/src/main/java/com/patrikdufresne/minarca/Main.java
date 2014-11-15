/**
 * Copyright(C) 2013 Patrik Dufresne Service Logiciel <info@patrikdufresne.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *         http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.patrikdufresne.minarca;

import static com.patrikdufresne.minarca.Localized._;

import java.util.Locale;

import org.eclipse.core.runtime.IStatus;
import org.eclipse.core.runtime.Status;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.util.ILogger;
import org.eclipse.jface.util.Policy;
import org.eclipse.jface.window.WindowManager;
import org.eclipse.swt.widgets.Display;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.ui.PreferenceDialog;
import com.patrikdufresne.minarca.ui.setup.SetupDialog;

/**
 * This class is the main entry point to the software.
 * 
 * @author Patrik Dufresne
 * 
 */
public class Main {

	static final transient Logger LOGGER = LoggerFactory.getLogger(Main.class);

	/**
	 * Return the current version.
	 * 
	 * @return
	 */
	public static String getCurrentVersion() {
		// Get the version from the package manifest
		return Main.class.getPackage().getImplementationVersion();
	}

	/**
	 * This function is the main entry point.
	 * 
	 * @param args
	 */
	public static void main(String[] args) {
		new Main().start(args);
	}

	/**
	 * This function is updating the JFace Policy error handler.
	 */
	protected static void updateJFacePolicy() {
		Policy.setLog(new ILogger() {

			@Override
			public void log(IStatus status) {
				switch (status.getSeverity()) {
				case IStatus.OK:
				case IStatus.INFO:
					if (status.getException() == null) {
						LOGGER.info(status.getMessage());
					} else {
						LOGGER.info(status.getMessage(), status.getException());
					}
					break;
				case IStatus.WARNING:
					if (status.getException() == null) {
						LOGGER.warn(status.getMessage());
					} else {
						LOGGER.warn(status.getMessage(), status.getException());
					}
					break;
				case IStatus.ERROR:
					if (status.getException() == null) {
						LOGGER.error(status.getMessage());
					} else {
						LOGGER.error(status.getMessage(), status.getException());
					}
					break;
				}
				System.err.println(status.getMessage());
				if (status.getException() != null) {
					status.getException().printStackTrace(System.err);
				}
			}
		});
	}

	protected void setDefaultImages() {
		// TODO Sets the default application Icon.
		// Image[] images = new Image[] {
		// Resources.getImage(Resources.APP_ICON_24),
		// Resources.getImage(Resources.APP_ICON_128) };
		// Window.setDefaultImages(images);
	}

	/**
	 * This function start the application.
	 * 
	 * @param args
	 */
	private void start(String[] args) {

		// Sets the local
		Locale.setDefault(Locale.CANADA_FRENCH);

		Display.setAppName(_("minarca"));
		final Display display = new Display();

		// Sets default windows images
		setDefaultImages();

		// Update logger
		updateJFacePolicy();

		// Check if configured.
		if (!API.INSTANCE.isConfigured()) {
			// If not configured, show wizard.
			if (!SetupDialog.open(null)) {
				// If user cancel, lose application.
				return;
			}
		}

		WindowManager winManager = new WindowManager();
		try {
			// Open Main Window
			PreferenceDialog win = new PreferenceDialog();
			win.setWindowManager(winManager);
			win.open();
			// Event loop
			while (winManager.getWindowCount() > 0) {
				try {
					if (!display.readAndDispatch())
						display.sleep();
				} catch (RuntimeException e) {
					Policy.getStatusHandler().show(
							new Status(IStatus.ERROR, _("minarca"),
									e.getMessage(), e), null);
				}
			}
		} catch (Exception e) {
			MessageDialog.openWarning(null, _("minarca"), e.getMessage());
		} finally {
			winManager.close();
			display.dispose();
		}

	}
}
