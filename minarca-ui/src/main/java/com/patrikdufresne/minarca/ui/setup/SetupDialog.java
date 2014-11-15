package com.patrikdufresne.minarca.ui.setup;

import static com.patrikdufresne.minarca.Localized._;

import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.window.Window;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.SelectionAdapter;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.graphics.Point;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Shell;
import org.eclipse.swt.widgets.Text;
import org.eclipse.ui.forms.widgets.Form;
import org.eclipse.ui.forms.widgets.FormText;
import org.eclipse.ui.forms.widgets.TableWrapData;
import org.eclipse.ui.forms.widgets.TableWrapLayout;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.ApplicationException;
import com.patrikdufresne.minarca.core.Client;
import com.patrikdufresne.minarca.ui.AppFormToolkit;

public class SetupDialog extends Dialog {

	private static final transient Logger LOGGER = LoggerFactory
			.getLogger(SetupDialog.class);

	public static boolean open(Shell parentShell) {

		SetupDialog dlg = new SetupDialog(parentShell);
		dlg.setBlockOnOpen(true);
		return dlg.open() == Window.OK;

	}

	private Client client;

	private Composite comp;

	private AppFormToolkit ft;

	protected SetupDialog(Shell parentShell) {
		super(parentShell);
	}

	@Override
	protected void configureShell(Shell newShell) {
		super.configureShell(newShell);
		newShell.setText(_("minarca"));
	}

	@Override
	protected Control createContents(Composite parent) {

		this.ft = new AppFormToolkit(parent.getDisplay());

		// Create the Form.
		Form form = ft.createForm(parent);

		// create the top level composite for the dialog
		// Composite composite = new Composite(parent, 0);
		GridLayout layout = new GridLayout();
		layout.marginHeight = 0;
		layout.marginWidth = 0;
		layout.verticalSpacing = 0;
		form.getBody().setLayout(layout);
		form.setLayoutData(new GridData(GridData.FILL_BOTH));
		// applyDialogFont(composite);
		// initialize the dialog units
		// initializeDialogUnits(composite);
		// create the dialog area and button bar
		dialogArea = createDialogArea(form.getBody());
		// buttonBar = createButtonBar(form.getBody());

		return form;
	}

	@Override
	protected Control createDialogArea(Composite parent) {

		this.comp = ft.createComposite(parent, SWT.NONE);
		this.comp.setLayoutData(new GridData(GridData.FILL_BOTH));
		TableWrapLayout layout = new TableWrapLayout();
		layout.topMargin = layout.rightMargin = layout.bottomMargin = layout.leftMargin = 25;
		this.comp.setLayout(layout);

		createPage1(this.comp);

		return comp;

	}

	private void createPage1(Composite parent) {
		// Dispose previous page.
		disposeChildren(parent);

		// App name
		Label appnameLabel = ft.createAppnameLabel(parent, _("minarca"),
				SWT.CENTER);
		appnameLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

		// Alert label.
		final FormText alertLabel = ft.createFormText(parent, "", true);
		alertLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

		// Introduction message
		String introText = _("<h2>Sign In</h2><br/>"
				+ "If you have an Minarca account,"
				+ "enter your username and password.");
		FormText introLabel = ft.createFormText(parent, introText, false);
		introLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

		// Username
		final Text usernameText = ft.createText(parent, "", SWT.BORDER);
		usernameText.setLayoutData(new TableWrapData(TableWrapData.FILL));
		usernameText.setMessage(_("Username"));
		usernameText.setFocus();

		// Password
		final Text passwordText = ft.createText(parent, "", SWT.BORDER
				| SWT.PASSWORD);
		passwordText.setLayoutData(new TableWrapData(TableWrapData.FILL));
		passwordText.setMessage(_("Password"));

		// Sign in button
		Button signInButton = ft.createButton(parent, _("Sign In"), SWT.PUSH);
		signInButton.setLayoutData(new TableWrapData(TableWrapData.FILL));
		getShell().setDefaultButton(signInButton);

		// Add event binding.
		signInButton.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {

				String username = usernameText.getText();
				String password = passwordText.getText();

				// Check credentials.
				String message = handleSignIn(username, password);
				if (message != null) {
					alertLabel.setText(message, true, true);
					alertLabel.getParent().layout();
					ft.decorateWarningLabel(alertLabel);
				} else {
					createPage2(comp);
				}

			}
		});

		// Relayout to update content.
		parent.layout();

	}

	private void createPage2(Composite parent) {
		// Dispose previous page.
		disposeChildren(parent);

		// App name
		Label appnameLabel = ft.createAppnameLabel(parent, _("minarca"),
				SWT.CENTER);
		appnameLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

		// Alert label.
		final FormText alertLabel = ft.createFormText(parent, "", true);
		alertLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

		// Introduction message
		String introText = _("<h2>Link your computer</h2><br/>"
				+ "You need to link this computer to your account. Please, "
				+ "provide a friendly name to represent it. "
				+ "Once selected, you won't be able to change it.<br/>"
				+ "<br/><b>Provide a computer name</b>");
		FormText introLabel = ft.createFormText(parent, introText, false);
		introLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

		// Computer name
		final Text computerNameText = ft.createText(parent, "", SWT.BORDER);
		computerNameText.setLayoutData(new TableWrapData(TableWrapData.FILL));
		computerNameText.setMessage(_("Computer name"));
		computerNameText.setText(API.INSTANCE.getDefaultComputerName());
		computerNameText.setFocus();

		// Sign in button
		Button signInButton = ft.createButton(parent, _("Sign In"), SWT.PUSH);
		signInButton.setLayoutData(new TableWrapData(TableWrapData.FILL));
		getShell().setDefaultButton(signInButton);

		// Add event binding.
		signInButton.addSelectionListener(new SelectionAdapter() {
			@Override
			public void widgetSelected(SelectionEvent e) {

				String computerName = computerNameText.getText();

				// Check credentials.
				String message = handleRegisterComputer(computerName);
				if (message != null) {
					alertLabel.setText(message, true, true);
					alertLabel.getParent().layout();
					ft.decorateWarningLabel(alertLabel);
				}

			}

		});

		// Relayout to update content.
		parent.layout();

	}

	/**
	 * Used to dispose every children of the given composite
	 * 
	 * @param composite
	 */
	private void disposeChildren(Composite composite) {
		Control[] children = composite.getChildren();
		for (Control c : children) {
			c.dispose();
		}
	}

	@Override
	protected Point getInitialSize() {
		// Sets fixed window size.
		return new Point(375, 575);
	}

	/**
	 * Called to handle user sign in.
	 * <p>
	 * This implementation will establish a connection via HTTP and or SSH to
	 * make sure the connection and credentials are valid.
	 * 
	 * @param username
	 *            the username for authentication
	 * @param password
	 *            the password for authentication.
	 * @return an error message or null if OK.
	 */
	protected String handleSignIn(String username, String password) {
		// Try to establish communication with HTTP first.
		try {
			this.client = API.INSTANCE.connect(username, password);
		} catch (ApplicationException e) {
			LOGGER.warn("fail to sign in", e);
			return e.getMessage();
		} catch (APIException e) {
			LOGGER.warn("fail to sign in", e);
			return _("Unknown error occurred !");
		}
		return null;
	}

	/**
	 * Called to handle computer registration.
	 * <p>
	 * This step is used to exchange the SSH keys.
	 * 
	 * @param computerName
	 *            the computer name.
	 * @return an error message or null if OK.
	 */
	protected String handleRegisterComputer(String computerName) {

		try {
			this.client.registerComputer(computerName);
		} catch (ApplicationException e) {
			LOGGER.warn("fail to register computer", e);
			return e.getMessage();
		} catch (APIException e) {
			LOGGER.warn("fail to register computer", e);
			return _("Unknown error occurred !");
		}
		return null;

	}

}
