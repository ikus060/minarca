/*
 * Copyright (c) 2014, Patrik Dufresne Service Logiciel. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.ui;

import static com.patrikdufresne.minarca.Localized._;

import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.resource.JFaceResources;
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
import org.eclipse.ui.forms.widgets.Hyperlink;
import org.eclipse.ui.forms.widgets.TableWrapData;
import org.eclipse.ui.forms.widgets.TableWrapLayout;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.Main;
import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.core.APIException;
import com.patrikdufresne.minarca.core.APIException.ApplicationException;
import com.patrikdufresne.minarca.core.Client;
import com.patrikdufresne.minarca.core.internal.OSUtils;

/**
 * Dialog used to configure the application the first time the user open it. It's similar to a wizard.
 * 
 * @author Patrik Dufresne
 * 
 */
public class SetupDialog extends Dialog {

    private static final transient Logger LOGGER = LoggerFactory.getLogger(SetupDialog.class);

    /**
     * Open this dialog.
     * 
     * @param parentShell
     * @return True if the setup is a success. False if cancel by user.
     */
    public static boolean open(Shell parentShell) {
        SetupDialog dlg = new SetupDialog(parentShell);
        dlg.setBlockOnOpen(true);
        return dlg.open() == Window.OK;
    }

    /**
     * Connection to minarca.
     */
    private Client client;
    /**
     * The composite holding the page.
     */
    private Composite comp;
    /**
     * Form tool kit to provide a webpage style.
     */
    private AppFormToolkit ft;

    /**
     * Default constructor
     * 
     * @param parentShell
     */
    protected SetupDialog(Shell parentShell) {
        super(parentShell);
    }

    /**
     * Add a ticlet to the dialog.
     */
    @Override
    protected void configureShell(Shell newShell) {
        super.configureShell(newShell);
        newShell.setText(_("Setup minarca"));
    }

    /**
     * Replace the default implementation to create a Form
     */
    @Override
    protected Control createContents(Composite parent) {

        this.ft = new AppFormToolkit(parent.getDisplay(), false);

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
        // create the dialog area and button bar
        dialogArea = createDialogArea(form.getBody());

        return form;
    }

    /**
     * Create the first page.
     */
    @Override
    protected Control createDialogArea(Composite parent) {

        this.comp = ft.createComposite(parent, SWT.NONE);
        this.comp.setLayoutData(new GridData(GridData.FILL_BOTH));
        TableWrapLayout layout = new TableWrapLayout();
        layout.topMargin = layout.bottomMargin = 5;
        layout.rightMargin = layout.leftMargin = 25;
        this.comp.setLayout(layout);

        createPage1(this.comp);

        return comp;

    }

    /**
     * Page used to sign-in, check credentials.
     * 
     * @param parent
     */
    private void createPage1(Composite parent) {
        // Dispose previous page.
        disposeChildren(parent);

        // App name
        Label appnameLabel = ft.createAppnameLabel(parent, _("minarca"), SWT.CENTER);
        appnameLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // App icon
        Label icon = this.ft.createLabel(parent, null);
        icon.setImage(JFaceResources.getImage(Main.MINARCA_128_PNG));
        icon.setLayoutData(new TableWrapData(TableWrapData.CENTER));

        // Introduction message
        String introText = "<h2>" + _("Sign In") + "</h2><br/>";
        introText += _("If you have an minarca account, " + "enter your username and password.");
        FormText introLabel = ft.createFormText(parent, introText, false);
        introLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Username
        final Text usernameText = ft.createText(parent, "", SWT.BORDER);
        usernameText.setLayoutData(new TableWrapData(TableWrapData.FILL));
        usernameText.setMessage(_("Username"));
        usernameText.setFocus();

        // Password
        final Text passwordText = ft.createText(parent, "", SWT.PASSWORD | SWT.BORDER);
        passwordText.setLayoutData(new TableWrapData(TableWrapData.FILL));
        passwordText.setMessage(_("Password"));

        // Sign in button
        Button signInButton = ft.createButton(parent, _("Sign In"), SWT.PUSH);
        signInButton.setLayoutData(new TableWrapData(TableWrapData.FILL));
        getShell().setDefaultButton(signInButton);

        // Alert label.
        final FormText alertLabel = ft.createFormText(parent, "", true);
        alertLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

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

    /**
     * Page used to link the computer (SSH key exchange).
     * 
     * @param parent
     */
    private void createPage2(Composite parent) {
        // Dispose previous page.
        disposeChildren(parent);

        // App name
        Label appnameLabel = ft.createAppnameLabel(parent, _("minarca"), SWT.CENTER);
        appnameLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // App icon
        Label icon = this.ft.createLabel(parent, null);
        icon.setImage(JFaceResources.getImage(Main.MINARCA_128_PNG));
        icon.setLayoutData(new TableWrapData(TableWrapData.CENTER));

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
        computerNameText.setText(OSUtils.COMPUTER_NAME);
        computerNameText.setFocus();

        // Sign in button
        Button linkButton = ft.createButton(parent, _("Link computer"), SWT.PUSH);
        linkButton.setLayoutData(new TableWrapData(TableWrapData.FILL));
        getShell().setDefaultButton(linkButton);

        // Alert label.
        final FormText alertLabel = ft.createFormText(parent, "", true);
        alertLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Add event binding.
        linkButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {

                String computerName = computerNameText.getText();

                // Check credentials.
                String message = handleLinkComputer(computerName);
                if (message != null) {
                    alertLabel.setText(message, true, true);
                    alertLabel.getParent().layout();
                    ft.decorateWarningLabel(alertLabel);
                } else {
                    createPage3(comp);
                }

            }

        });

        // Relayout to update content.
        parent.layout();

    }

    /**
     * Page used to show sucessful config.
     * 
     * @param parent
     */
    private void createPage3(Composite parent) {
        // Dispose previous page.
        disposeChildren(parent);

        // App name
        Label appnameLabel = ft.createAppnameLabel(parent, _("minarca"), SWT.CENTER);
        appnameLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // App icon
        Label icon = this.ft.createLabel(parent, null);
        icon.setImage(JFaceResources.getImage(Main.MINARCA_128_PNG));
        icon.setLayoutData(new TableWrapData(TableWrapData.CENTER));

        // Introduction message
        String introText = "<h2>" + _("Success !") + "</h2><br/>";
        introText += _("Your computer is now configure to backup it self once a day with minarca!");
        FormText introLabel = ft.createFormText(parent, introText, false);
        introLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Sign in button
        Button linkButton = ft.createButton(parent, _("Close"), SWT.PUSH);
        linkButton.setLayoutData(new TableWrapData(TableWrapData.FILL));
        getShell().setDefaultButton(linkButton);

        // Add event binding.
        linkButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                // Close the setup dialog.
                close();
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

    /**
     * Return a fixed dialog size.
     */
    @Override
    protected Point getInitialSize() {
        // Sets fixed window size.
        return new Point(325, 575);
    }

    /**
     * Called to handle user sign in.
     * <p>
     * This implementation will establish a connection via HTTP and or SSH to make sure the connection and credentials
     * are valid.
     * 
     * @param username
     *            the username for authentication
     * @param password
     *            the password for authentication.
     * @return an error message or null if OK.
     */
    protected String handleSignIn(String username, String password) {
        // Try to establish communication with HTTP first.
        LOGGER.info("sign in as {}", username);
        try {
            this.client = API.instance().connect(username, password);
            // If credentials are valid, safe the username
            API.instance().setUsername(username);
        } catch (ApplicationException e) {
            LOGGER.warn("fail to sign in", e);
            return e.getMessage();
        } catch (APIException e) {
            LOGGER.warn("fail to sign in", e);
            return _("Unknown error occurred!");
        }
        return null;
    }

    /**
     * Called to handle computer registration.
     * <p>
     * This step is used to exchange the SSH keys.
     * 
     * @param name
     *            the computer name.
     * @return an error message or null if OK.
     */
    protected String handleLinkComputer(String name) {
        // Link the computer
        LOGGER.info("link computer {}", name);
        try {
            this.client.link(name);
        } catch (ApplicationException e) {
            LOGGER.warn("fail to register computer", e);
            return e.getMessage();
        } catch (APIException e) {
            LOGGER.warn("fail to register computer", e);
            return _("<strong>Unknown error occurred !</strong> If the problem persists, try to re-install mirarca.");
        } catch (IllegalArgumentException e) {
            LOGGER.warn("invalid computername: " + name, e);
            return _("Invalid computer name !");
        }

        // Set other settings to default.
        LOGGER.info("set default config");
        try {
            API.instance().defaultConfig();
        } catch (APIException e) {
            LOGGER.warn("fail to schedule task", e);
            return _("Can't schedule backup task ! If the problem persists, try to re-install mirarca.");
        }

        return null;

    }

}
