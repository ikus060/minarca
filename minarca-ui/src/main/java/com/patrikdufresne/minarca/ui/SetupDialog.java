/*
 * Copyright (C) 2015, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.ui;

import static com.patrikdufresne.minarca.Localized._;

import java.io.IOException;

import org.apache.commons.lang3.SystemUtils;
import org.apache.commons.lang3.mutable.MutableInt;
import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.jface.dialogs.ProgressIndicator;
import org.eclipse.jface.layout.PixelConverter;
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
import org.eclipse.swt.widgets.Display;
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
import com.patrikdufresne.minarca.core.APIException.ComputerNameAlreadyInUseException;
import com.patrikdufresne.minarca.core.internal.Compat;
import com.patrikdufresne.rdiffweb.core.Client;

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
        // ft.paintBordersFor(this.comp);

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
        // JFaceResources.getImageRegistry().put(Main.MINARCA_128_PNG, ImageDescriptor.createFromFile(Main.class,
        // Main.MINARCA_128_PNG));
        icon.setImage(JFaceResources.getImage(Images.MINARCA_128_PNG));
        icon.setLayoutData(new TableWrapData(TableWrapData.CENTER));

        // Introduction message
        String introText = "<h2>" + _("Sign In") + "</h2><br/>";
        introText += _("If you have a minarca account, enter your username and password.");
        FormText introLabel = ft.createFormText(parent, introText, false);
        introLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Alert label.
        final FormText alertLabel = ft.createFormText(parent, "", true);
        alertLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

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

        // Spacer
        Composite spacer = ft.createComposite(parent);
        TableWrapData layoutdata = new TableWrapData(TableWrapData.FILL);
        layoutdata.heightHint = 10;
        spacer.setLayoutData(layoutdata);

        // Request account
        String subscribeText = "<b>" + _("Create account") + "</b><br/>";
        subscribeText += _("If you don't have a minarca account, you may subscribe by filling the online form.");
        subscribeText += "<br/><a href='" + _("http://www.patrikdufresne.com/en/minarca/subscribe") + "'>";
        subscribeText += _("Subscribe...") + "</a>";
        FormText subscribeLabel = ft.createFormText(parent, subscribeText, false);
        subscribeLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

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
        icon.setImage(JFaceResources.getImage(Images.MINARCA_128_PNG));
        icon.setLayoutData(new TableWrapData(TableWrapData.CENTER));

        // Introduction message
        String introText = "<h2>" + _("Link your computer") + "</h2><br/>";
        introText += _("You need to link this computer to your account. Please, "
                + "provide a friendly name to represent it. "
                + "Once selected, you won't be able to change it.");
        FormText introLabel = ft.createFormText(parent, introText, false);
        introLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Alert label.
        final FormText alertLabel = ft.createFormText(parent, "", true);
        alertLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Label
        String computerNameLabelText = "<b>" + _("Provide a computer name") + "</b>";
        FormText computerNameLabel = ft.createFormText(parent, computerNameLabelText, false);
        computerNameLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Computer name
        final Text computerNameText = ft.createText(parent, "", SWT.BORDER);
        computerNameText.setLayoutData(new TableWrapData(TableWrapData.FILL));
        computerNameText.setMessage(_("Computer name"));
        computerNameText.setText(Compat.COMPUTER_NAME);
        computerNameText.setFocus();

        // Sign in button
        final Button linkButton = ft.createButton(parent, _("Link computer"), SWT.PUSH);
        linkButton.setLayoutData(new TableWrapData(TableWrapData.FILL));
        getShell().setDefaultButton(linkButton);

        // Progress bar
        final ProgressIndicator progress = new ProgressIndicator(parent);
        ft.adapt(progress);
        progress.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Add event binding.
        linkButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                // What a mess. Blame Java.
                final String computerName = computerNameText.getText();
                linkButton.setEnabled(false);
                progress.beginAnimatedTask();

                // Start the processing.
                new Thread() {
                    public void run() {
                        final String message = handleLinkComputer(computerName, false);
                        Display.getDefault().asyncExec(new Runnable() {
                            @Override
                            public void run() {
                                progress.done();
                                if (message != null) {
                                    linkButton.setEnabled(true);
                                    alertLabel.setText(message, true, true);
                                    alertLabel.getParent().layout();
                                    ft.decorateWarningLabel(alertLabel);
                                } else {
                                    createPage3(comp);
                                }
                            }
                        });
                    }
                }.start();
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
        icon.setImage(JFaceResources.getImage(Images.MINARCA_128_PNG));
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
        if (SystemUtils.IS_OS_WINDOWS) {
            return new Point(325, 575);
        } else {
            // Sets fixed window size.
            PixelConverter pc = new PixelConverter(this.getShell());
            int height = pc.convertVerticalDLUsToPixels(235);
            int width = pc.convertHorizontalDLUsToPixels(195);
            return new Point(width, height);
        }
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
    protected String handleLinkComputer(String name, boolean force) {
        // Little validation before
        if (name.trim().isEmpty()) {
            return _("Computer name cannot be empty.");
        }
        LOGGER.info("link computer {}", name);
        try {
            API.instance().link(name, this.client, force);
        } catch (ComputerNameAlreadyInUseException e) {
            final MutableInt returnCode = new MutableInt();
            Display.getCurrent().syncExec(new Runnable() {
                @Override
                public void run() {
                    int r = DetailMessageDialog.openYesNoQuestion(
                            getShell(),
                            Display.getAppName(),
                            _("Are you sure you want to keep the given computer name ?"),
                            _("The given computer name is already in use in minarca. "
                                    + "You may keep this computer name if the name is "
                                    + "no longer used by another computer currently "
                                    + "link to minarca."),
                            null).getReturnCode();
                    returnCode.setValue(r);
                }
            });
            if (returnCode.intValue() == IDialogConstants.YES_ID) {
                // Force usage of the computer name
                return handleLinkComputer(name, true);
            }
            return _("Change the computer name");
        } catch (APIException e) {
            LOGGER.warn("fail to register computer", e);
            return e.getMessage();
        } catch (IllegalArgumentException e) {
            LOGGER.warn("invalid computername: " + name, e);
            return _("Should only contains letters, numbers, dash (-) and dot (.)");
        } catch (Exception e) {
            LOGGER.warn("fail to register computer", e);
            return _("<strong>Unknown error occurred!</strong> If the problem persists, try to re-install mirarca.");
        }

        // Set other settings to default.
        LOGGER.info("set default config");
        try {
            API.instance().defaultConfig(true);
        } catch (APIException e) {
            LOGGER.warn("fail to schedule task", e);
            return _("Can't schedule backup task! If the problem persists, try to re-install mirarca.");
        }
        return null;
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
        // Check little validation of the username password.
        if (username.trim().isEmpty()) {
            return _("Username cannot be empty.");
        }
        if (password.trim().isEmpty()) {
            return _("Password cannot be empty.");
        }
        // Try to establish communication with HTTP first.
        LOGGER.info("sign in as [{}]", username);
        try {
            this.client = API.instance().connect(username, password);
        } catch (APIException e) {
            LOGGER.warn("fail to sign in", e);
            return e.getMessage();
        } catch (IOException e) {
            LOGGER.warn("fail to sign in", e);
            return _("Can't validate your credentials. Please check your connectivity.");
        } catch (Exception e) {
            LOGGER.warn("fail to sign in", e);
            return _("Unknown error occurred!");
        }
        return null;
    }

}
