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
package com.patrikdufresne.minarca.ui;

import java.io.PrintWriter;
import java.io.StringWriter;

import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.jface.dialogs.IconAndMessageDialog;
import org.eclipse.jface.dialogs.MessageDialog;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.swt.SWT;
import org.eclipse.swt.dnd.Clipboard;
import org.eclipse.swt.dnd.TextTransfer;
import org.eclipse.swt.dnd.Transfer;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.events.SelectionListener;
import org.eclipse.swt.graphics.Image;
import org.eclipse.swt.graphics.Point;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Menu;
import org.eclipse.swt.widgets.MenuItem;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.swt.widgets.Text;

/**
 * This class display a message dialog with a message, a short detail message
 * and a long detail message. It's useful to provide different level of
 * information to the user.
 * 
 * @author Patrik Dufresne
 * 
 */
public class DetailMessageDialog extends MessageDialog {

	/**
	 * Convenience method to open a standard error dialog without long detail
	 * message.
	 * 
	 * @param parent
	 *            the parent shell of the dialog, or <code>null</code> if none
	 * @param title
	 *            the dialog's title, or <code>null</code> if none
	 * @param message
	 *            a general message
	 * @param shortDetail
	 *            a show details message to give more precision about the error
	 * @return the dialog, after being closed by the user, which the client can
	 *         only call <code>getReturnCode()</code> or
	 *         <code>getToggleState()</code>
	 */
	public static DetailMessageDialog openError(Shell parent,
			String title, String message, String shortDetail) {
		return openError(parent, title, message, shortDetail,
				(String) null);
	}

	/**
	 * Convenience method to open a standard error dialog.
	 * 
	 * @param parent
	 *            the parent shell of the dialog, or <code>null</code> if none
	 * @param title
	 *            the dialog's title, or <code>null</code> if none
	 * @param message
	 *            the message
	 * @param shortDetail
	 *            a show details message to give more precision about the error
	 * @param longDetail
	 *            a long description of the error.
	 * @return the dialog, after being closed by the user, which the client can
	 *         only call <code>getReturnCode()</code> or
	 *         <code>getToggleState()</code>
	 */
	public static DetailMessageDialog openError(Shell parent,
			String title, String message, String shortDetail, String longDetail) {
		DetailMessageDialog dialog = new DetailMessageDialog(parent, title,
				null, message, shortDetail, longDetail, ERROR,
				new String[] { IDialogConstants.OK_LABEL }, 0);
		dialog.open();
		return dialog;
	}

	/**
	 * Convenience method to open a standard error dialog.
	 * 
	 * @param parent
	 *            the parent shell of the dialog, or <code>null</code> if none
	 * @param title
	 *            the dialog's title, or <code>null</code> if none
	 * @param message
	 *            a general message
	 * @param shortDetail
	 *            a show details message to give more precision about the error
	 * @param longDetail
	 *            the exception to show
	 * @return the dialog, after being closed by the user, which the client can
	 *         only call <code>getReturnCode()</code> or
	 *         <code>getToggleState()</code>
	 */
	public static DetailMessageDialog openError(Shell parent,
			String title, String message, String shortDetail,
			Throwable longDetail) {
		StringWriter sw = new StringWriter();
		longDetail.printStackTrace(new PrintWriter(sw));
		return openError(parent, title, message, shortDetail,
				sw.toString());
	}

	/**
	 * Convenience method to open a standard information dialog.
	 * 
	 * @param parent
	 *            the parent shell of the dialog, or <code>null</code> if none
	 * @param title
	 *            the dialog's title, or <code>null</code> if none
	 * @param message
	 *            the message
	 * @param shortDetail
	 *            a show details message to give more precision about the error
	 * @return the dialog, after being closed by the user, which the client can
	 *         only call <code>getReturnCode()</code> or
	 *         <code>getToggleState()</code>
	 */
	public static DetailMessageDialog openInformation(Shell parent,
			String title, String message, String shortDetail) {
		return openInformation(parent, title, message, shortDetail,
				(String) null);
	}

	/**
	 * Convenience method to open a standard information dialog.
	 * 
	 * @param parent
	 *            the parent shell of the dialog, or <code>null</code> if none
	 * @param title
	 *            the dialog's title, or <code>null</code> if none
	 * @param message
	 *            the message
	 * @param shortDetail
	 *            a show details message to give more precision about the
	 *            warning
	 * @param longDetail
	 *            a long description of the warning.
	 * @return the dialog, after being closed by the user, which the client can
	 *         only call <code>getReturnCode()</code> or
	 *         <code>getToggleState()</code>
	 */
	public static DetailMessageDialog openInformation(Shell parent,
			String title, String message, String shortDetail, String longDetail) {
		DetailMessageDialog dialog = new DetailMessageDialog(parent, title,
				null, message, shortDetail, longDetail, INFORMATION,
				new String[] { IDialogConstants.OK_LABEL }, 0);
		dialog.open();
		return dialog;
	}

	/**
	 * Convenience method to open a standard information dialog.
	 * 
	 * @param parent
	 *            the parent shell of the dialog, or <code>null</code> if none
	 * @param title
	 *            the dialog's title, or <code>null</code> if none
	 * @param message
	 *            the message
	 * @param shortDetail
	 *            a show details message to give more precision about the error
	 * @param longDetail
	 *            the exception to show
	 * @return the dialog, after being closed by the user, which the client can
	 *         only call <code>getReturnCode()</code> or
	 *         <code>getToggleState()</code>
	 */
	public static DetailMessageDialog openInformation(Shell parent,
			String title, String message, String shortDetail,
			Throwable longDetail) {
		StringWriter sw = new StringWriter();
		longDetail.printStackTrace(new PrintWriter(sw));
		return openInformation(parent, title, message, shortDetail,
				sw.toString());
	}

	/**
	 * Convenience method to open a simple confirm (OK/Cancel) dialog.
	 * 
	 * @param parent
	 *            the parent shell of the dialog, or <code>null</code> if none
	 * @param title
	 *            the dialog's title, or <code>null</code> if none
	 * @param message
	 *            the message
	 * @param toggleMessage
	 *            the message for the toggle control, or <code>null</code> for
	 *            the default message
	 * @param toggleState
	 *            the initial state for the toggle
	 * @param store
	 *            the IPreference store in which the user's preference should be
	 *            persisted; <code>null</code> if you don't want it persisted
	 *            automatically.
	 * @param key
	 *            the key to use when persisting the user's preference;
	 *            <code>null</code> if you don't want it persisted.
	 * @return the dialog, after being closed by the user, which the client can
	 *         only call <code>getReturnCode()</code> or
	 *         <code>getToggleState()</code>
	 */
	public static DetailMessageDialog openOkCancelConfirm(Shell parent,
			String title, String message, String shortDetail, String longDetail) {
		DetailMessageDialog dialog = new DetailMessageDialog(parent, title,
				null, message, shortDetail, longDetail, QUESTION, new String[] {
						IDialogConstants.OK_LABEL,
						IDialogConstants.CANCEL_LABEL }, 0);
		dialog.open();
		return dialog;
	}

	/**
	 * Convenient method to open a standard warning dialog without long
	 * description message.
	 * 
	 * @param parent
	 *            the parent shell of the dialog, or <code>null</code> if none
	 * @param title
	 *            the dialog's title, or <code>null</code> if none
	 * @param message
	 *            the message
	 * @return the dialog, after being closed by the user, which the client can
	 *         only call <code>getReturnCode()</code> or
	 *         <code>getToggleState()</code>
	 */
	public static DetailMessageDialog openWarning(Shell parent,
			String title, String message, String shortDetail) {
		return openWarning(parent, title, message, shortDetail,
				(String) null);
	}

	/**
	 * Convenient method to open a standard warning dialog.
	 * 
	 * @param parent
	 *            the parent shell of the dialog, or <code>null</code> if none
	 * @param title
	 *            the dialog's title, or <code>null</code> if none
	 * @param message
	 *            the message
	 * @return the dialog, after being closed by the user, which the client can
	 *         only call <code>getReturnCode()</code> or
	 *         <code>getToggleState()</code>
	 */
	public static DetailMessageDialog openWarning(Shell parent,
			String title, String message, String shortDetail, String longDetail) {
		DetailMessageDialog dialog = new DetailMessageDialog(parent, title,
				null, message, shortDetail, longDetail, WARNING,
				new String[] { IDialogConstants.OK_LABEL }, 0);
		dialog.open();
		return dialog;
	}

	/**
	 * Convenient method to open a standard warning dialog without long
	 * description message.
	 * 
	 * @param parent
	 *            the parent shell of the dialog, or <code>null</code> if none
	 * @param title
	 *            the dialog's title, or <code>null</code> if none
	 * @param message
	 *            the message
	 * @return the dialog, after being closed by the user, which the client can
	 *         only call <code>getReturnCode()</code> or
	 *         <code>getToggleState()</code>
	 */
	public static DetailMessageDialog openWarning(Shell parent,
			String title, String message, String shortDetail,
			Throwable longDetail) {
		StringWriter sw = new StringWriter();
		longDetail.printStackTrace(new PrintWriter(sw));
		return openWarning(parent, title, message, shortDetail,
				sw.toString());
	}

	/**
	 * Convenience method to open a simple question Yes/No/Cancel dialog.
	 * 
	 * @param parent
	 *            the parent shell of the dialog, or <code>null</code> if none
	 * @param title
	 *            the dialog's title, or <code>null</code> if none
	 * @param message
	 *            the message
	 * @param toggleMessage
	 *            the message for the toggle control, or <code>null</code> for
	 *            the default message
	 * @param toggleState
	 *            the initial state for the toggle
	 * @param store
	 *            the IPreference store in which the user's preference should be
	 *            persisted; <code>null</code> if you don't want it persisted
	 *            automatically.
	 * @param key
	 *            the key to use when persisting the user's preference;
	 *            <code>null</code> if you don't want it persisted.
	 * @return the dialog, after being closed by the user, which the client can
	 *         only call <code>getReturnCode()</code> or
	 *         <code>getToggleState()</code>
	 */
	public static DetailMessageDialog openYesNoCancelQuestion(
			Shell parent, String title, String message, String shortDetail,
			String longDetail) {
		DetailMessageDialog dialog = new DetailMessageDialog(parent, title,
				null, message, shortDetail, longDetail, QUESTION, new String[] {
						IDialogConstants.YES_LABEL, IDialogConstants.NO_LABEL,
						IDialogConstants.CANCEL_LABEL }, 0);
		dialog.open();
		return dialog;
	}

	/**
	 * Convenience method to open a simple Yes/No question dialog.
	 * 
	 * @param parent
	 *            the parent shell of the dialog, or <code>null</code> if none
	 * @param title
	 *            the dialog's title, or <code>null</code> if none
	 * @param message
	 *            the message
	 * @param shortDetail
	 * @param longDetail
	 * 
	 * @return the dialog, after being closed by the user, which the client can
	 *         only call <code>getReturnCode()</code> or
	 *         <code>getToggleState()</code>
	 */
	public static DetailMessageDialog openYesNoQuestion(Shell parent,
			String title, String message, String shortDetail, String longDetail) {
		DetailMessageDialog dialog = new DetailMessageDialog(parent, title,
				null, message, shortDetail, longDetail, QUESTION,
				new String[] { IDialogConstants.YES_LABEL,
						IDialogConstants.NO_LABEL }, 0);
		dialog.open();
		return dialog;
	}

	/**
	 * The current clipboard. To be disposed when closing the dialog.
	 */
	private Clipboard clipboard;
	/**
	 * The detail message
	 */
	private String detailMessage;
	/**
	 * The widget to display the detail message
	 */
	protected Label detailMessageLabel;
	/**
	 * The main status object.
	 */
	private String details;
	/**
	 * The Details button.
	 */
	private Button detailsButton;
	/**
	 * Indicates whether the error details viewer is currently created.
	 */
	private boolean detailsCreated = false;
	/**
	 * The SWT list control that displays the error details.
	 */
	protected Text detailsText;

	/**
	 * Creates a message dialog with a toggle and detailed message. See the
	 * superclass constructor for info on the other parameters.
	 * 
	 * @param parentShell
	 *            the parent shell
	 * @param dialogTitle
	 *            the dialog title, or <code>null</code> if none
	 * @param image
	 *            the dialog title image, or <code>null</code> if none
	 * @param message
	 *            the dialog message.
	 * @param detailMessage
	 *            a short detail message.
	 * @param details
	 *            the full message details. e.g.: stacktrace
	 * @param dialogImageType
	 *            one of the following values:
	 *            <ul>
	 *            <li><code>MessageDialog.NONE</code> for a dialog with no image
	 *            </li>
	 *            <li><code>MessageDialog.ERROR</code> for a dialog with an
	 *            error image</li>
	 *            <li><code>MessageDialog.INFORMATION</code> for a dialog with
	 *            an information image</li>
	 *            <li><code>MessageDialog.QUESTION </code> for a dialog with a
	 *            question image</li>
	 *            <li><code>MessageDialog.WARNING</code> for a dialog with a
	 *            warning image</li>
	 *            </ul>
	 * @param dialogButtonLabels
	 *            an array of labels for the buttons in the button bar
	 * @param defaultIndex
	 *            the index in the button label array of the default button
	 * @param toggleMessage
	 *            the message for the toggle control, or <code>null</code> for
	 *            the default message
	 * @param toggleState
	 *            the initial state for the toggle
	 * 
	 */
	public DetailMessageDialog(Shell parentShell, String dialogTitle,
			Image image, String message, String detailMessage, String details,
			int dialogImageType, String[] dialogButtonLabels, int defaultIndex) {

		super(parentShell, dialogTitle, image, message, dialogImageType,
				dialogButtonLabels, defaultIndex);

		this.detailMessage = detailMessage;

		this.details = details;

	}

	@Override
	protected void buttonPressed(int id) {
		if (id == IDialogConstants.DETAILS_ID) {
			// was the details button pressed?
			toggleDetailsArea();
		} else {
			super.buttonPressed(id);
		}
	}

	@Override
	public boolean close() {
		if (this.clipboard != null) {
			this.clipboard.dispose();
		}
		return super.close();
	}

	/**
	 * Copy the contents of the statuses to the clipboard.
	 */
	void copyToClipboard() {
		if (this.clipboard != null) {
			this.clipboard.dispose();
		}
		this.clipboard = new Clipboard(this.detailsText.getDisplay());
		this.clipboard.setContents(new Object[] { this.details },
				new Transfer[] { TextTransfer.getInstance() });
	}

	@Override
	protected void createButtonsForButtonBar(Composite parent) {
		super.createButtonsForButtonBar(parent);
		createDetailsButton(parent);
	}

	/**
	 * Create the details button if it should be included.
	 * 
	 * @param parent
	 *            the parent composite
	 * 
	 */
	protected void createDetailsButton(Composite parent) {
		if (shouldShowDetailsButton()) {
			this.detailsButton = createButton(parent,
					IDialogConstants.DETAILS_ID,
					IDialogConstants.SHOW_DETAILS_LABEL, false);
		}
	}

	/**
	 * (non-Javadoc)
	 * 
	 */
	@Override
	protected Control createDialogArea(Composite parent) {
		Control control = super.createDialogArea(parent);
		if (control.getLayoutData() instanceof GridData) {
			((GridData) control.getLayoutData()).grabExcessHorizontalSpace = true;
			((GridData) control.getLayoutData()).grabExcessVerticalSpace = true;
		}
		return control;
	}

	/**
	 * Create this dialog's drop-down list component.
	 * 
	 * @param parent
	 *            the parent composite
	 * @return the drop-down list component
	 */
	protected Text createDropDownText(Composite parent) {
		// create the text
		this.detailsText = new Text(parent, SWT.BORDER | SWT.MULTI
				| SWT.READ_ONLY | SWT.WRAP);
		// fill the list
		this.detailsText.setText(this.details);
		GridData data = new GridData(SWT.FILL, SWT.FILL, true, true);
		data.horizontalSpan = 2;
		this.detailsText.setLayoutData(data);
		this.detailsText.setFont(parent.getFont());

		Menu copyMenu = new Menu(this.detailsText);
		MenuItem copyItem = new MenuItem(copyMenu, SWT.NONE);
		copyItem.addSelectionListener(new SelectionListener() {
			/*
			 * @see SelectionListener.widgetDefaultSelected(SelectionEvent)
			 */
			@Override
			public void widgetDefaultSelected(SelectionEvent e) {
				copyToClipboard();
			}

			/*
			 * @see SelectionListener.widgetSelected (SelectionEvent)
			 */
			@Override
			public void widgetSelected(SelectionEvent e) {
				copyToClipboard();
			}
		});
		copyItem.setText(JFaceResources.getString("copy")); //$NON-NLS-1$
		this.detailsText.setMenu(copyMenu);
		this.detailsCreated = true;
		return this.detailsText;
	}

	/**
	 * Creates and returns the contents of an area of the dialog which appears
	 * below the message and above the button bar.
	 * <p>
	 * The default implementation of this framework method returns
	 * <code>null</code>. Subclasses may override.
	 * </p>
	 * 
	 * @param parent
	 *            parent composite to contain the custom area
	 * @return the custom area control, or <code>null</code>
	 */
	@Override
	protected Control createMessageArea(Composite parent) {
		super.createMessageArea(parent);

		if (super.imageLabel != null) {
			super.imageLabel.setLayoutData(new GridData(SWT.FILL, SWT.FILL,
					false, false, 1, 2));
		}

		if (super.messageLabel != null) {
			super.messageLabel.setFont(JFaceResources.getBannerFont());
			GridData data = new GridData(SWT.FILL, SWT.FILL, true, false);
			data.widthHint = convertHorizontalDLUsToPixels(IDialogConstants.MINIMUM_MESSAGE_AREA_WIDTH);
			super.messageLabel.setLayoutData(data);
		}

		// Detail message
		if (this.detailMessage != null) {
			this.detailMessageLabel = new Label(parent, getMessageLabelStyle());
			this.detailMessageLabel.setText(this.detailMessage);
			GridData data = new GridData(SWT.FILL, SWT.FILL, true, false);
			data.widthHint = convertHorizontalDLUsToPixels(IDialogConstants.MINIMUM_MESSAGE_AREA_WIDTH);
			this.detailMessageLabel.setLayoutData(data);
		}

		return parent;
	}

	/**
	 * Return the short detail message.
	 * 
	 * @return
	 */
	protected String getDetailMessage() {
		return this.detailMessage;
	}

	/**
	 * Return the details value.
	 * 
	 * @return the details
	 */
	protected String getDetails() {
		return this.details;
	}

	/**
	 * Return the message value.
	 * 
	 * @return the message
	 * @see IconAndMessageDialog
	 */
	protected String getMessage() {
		return this.message;
	}

	@Override
	protected boolean isResizable() {
		return true;
	}

	/**
	 * Sets the short detail message. This function may be used by subclasses to
	 * redefine the original message value if it wasn't null.
	 * 
	 * @param value
	 *            the new detail message.
	 */
	protected void setDetailMessage(String value) {
		this.detailMessage = value == null ? "" : value; //$NON-NLS-1$
		if (this.detailMessageLabel == null
				|| this.detailMessageLabel.isDisposed()) {
			return;
		}
		this.detailMessageLabel.setText(this.detailMessage);
	}

	/**
	 * Sets the details. This function may be used by subclasses to redefine the
	 * original details value if it wasn't null.
	 * 
	 * @param value
	 *            the new details value
	 */
	protected void setDetails(String value) {
		this.details = value == null ? "" : value; //$NON-NLS-1$
		if (this.detailsText == null || this.detailsText.isDisposed()) {
			return;
		}
		this.detailsText.setText(this.details);
	}

	/**
	 * This method sets the message in the message label. This function may be
	 * called by subclasses to redefine the original message value if it wasn't
	 * null.
	 * 
	 * @param value
	 *            the String for the message area
	 * @see IconAndMessageDialog
	 */
	protected void setMessage(String value) {
		// must not set null text in a label
		this.message = value == null ? "" : value; //$NON-NLS-1$
		if (this.messageLabel == null || this.messageLabel.isDisposed()) {
			return;
		}
		this.messageLabel.setText(this.message);
	}

	/**
	 * Return whether the Details button should be included. This method is
	 * invoked once when the dialog is built. By default, the Details button is
	 * only included if the status used when creating the dialog was a
	 * multi-status or if the status contains an exception. Subclasses may
	 * override.
	 * 
	 * @return whether the Details button should be included
	 * 
	 */
	protected boolean shouldShowDetailsButton() {
		return this.details != null;
	}

	/**
	 * Toggles the unfolding of the details area. This is triggered by the user
	 * pressing the details button.
	 */
	protected void toggleDetailsArea() {
		Point windowSize = getShell().getSize();
		// Point oldSize = getShell().computeSize(windowSize.x, SWT.DEFAULT);
		if (this.detailsCreated) {
			this.detailsText.dispose();
			this.detailsCreated = false;
			this.detailsButton.setText(IDialogConstants.SHOW_DETAILS_LABEL);
			getContents().getShell().layout();
		} else {
			this.detailsText = createDropDownText((Composite) getContents());
			this.detailsButton.setText(IDialogConstants.HIDE_DETAILS_LABEL);
			getContents().getShell().layout();
		}
		Point newSize = getShell().computeSize(windowSize.x, SWT.DEFAULT);
		getShell().setSize(new Point(windowSize.x, newSize.y));
	}
}
