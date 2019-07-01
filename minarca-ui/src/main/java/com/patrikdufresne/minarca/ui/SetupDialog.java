/*
 * Copyright (C) 2018, Patrik Dufresne Service Logiciel inc. All rights reserved.
 * Patrik Dufresne Service Logiciel PROPRIETARY/CONFIDENTIAL.
 * Use is subject to license terms.
 */
package com.patrikdufresne.minarca.ui;

import static com.patrikdufresne.minarca.Localized._;

import java.io.IOException;

import org.apache.commons.lang3.StringUtils;
import org.apache.commons.lang3.Validate;
import org.apache.commons.lang3.mutable.MutableInt;
import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.jface.dialogs.ProgressIndicator;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.jface.window.Window;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.ModifyEvent;
import org.eclipse.swt.events.ModifyListener;
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
import com.patrikdufresne.minarca.core.APIException.RepositoryNameAlreadyInUseException;
import com.patrikdufresne.minarca.core.Client;
import com.patrikdufresne.minarca.core.internal.Compat;

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
        newShell.setText(_("Setup Minarca"));
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

        // Introduction message
        this.ft.createLabel(parent, _("Where's to backup your data ?"), AppFormToolkit.H3);

        // Remote server
        this.ft.createLabel(parent, _("Address"), AppFormToolkit.BOLD);
        final Text remoteserverText = ft.createText(parent, "", SWT.BORDER);
        remoteserverText.setLayoutData(new TableWrapData(TableWrapData.FILL));
        remoteserverText.setMessage(_("Remote server address e.g.: backup.example.com:8080"));
        remoteserverText.setToolTipText(_("Enter the remote server address. Either an ip address and port, or a URL."));
        remoteserverText.setFocus();
        this.ft.createLabel(parent, _("http[s]://hostname[:port]"), AppFormToolkit.SMALL);

        // Username & Password
        this.ft.createLabel(parent, _("Username"), AppFormToolkit.BOLD);
        final Text usernameText = ft.createText(parent, "", SWT.BORDER);
        usernameText.setLayoutData(new TableWrapData(TableWrapData.FILL));

        this.ft.createLabel(parent, _("Password"), AppFormToolkit.BOLD);
        final Text passwordText = ft.createText(parent, "", SWT.PASSWORD | SWT.BORDER);
        passwordText.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Sign in button
        final Button signInButton = ft.createButton(parent, _("Sign In"), SWT.PUSH);
        signInButton.setLayoutData(new TableWrapData(TableWrapData.FILL));
        signInButton.setEnabled(false);
        getShell().setDefaultButton(signInButton);

        // Enable Sing-In buttont when all field contains something.
        ModifyListener modifyListener = new ModifyListener() {

            @Override
            public void modifyText(ModifyEvent e) {
                String remoteserver = remoteserverText.getText();
                String username = usernameText.getText();
                String password = passwordText.getText();
                signInButton.setEnabled(StringUtils.isNotBlank(remoteserver) && StringUtils.isNotBlank(username) && StringUtils.isNotBlank(password));
            }
        };
        remoteserverText.addModifyListener(modifyListener);
        usernameText.addModifyListener(modifyListener);
        passwordText.addModifyListener(modifyListener);

        // Add event binding.
        signInButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                String remoteserver = remoteserverText.getText();
                String username = usernameText.getText();
                String password = passwordText.getText();
                if (handleSignIn(remoteserver, username, password)) {
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

        ((TableWrapLayout) parent.getLayout()).numColumns = 1;

        // App name
        Label appnameLabel = ft.createAppnameLabel(parent, _("Minarca"), SWT.CENTER);
        appnameLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // App icon
        Label icon = this.ft.createLabel(parent, null);
        icon.setImage(JFaceResources.getImage(Images.MINARCA_128_PNG));
        icon.setLayoutData(new TableWrapData(TableWrapData.CENTER));

        // Introduction message
        String introText = "<h2>" + _("Link your system") + "</h2><br/>";
        introText += _("You need to link this system to your account. Please, "
                + "provide a friendly name to represent it. "
                + "Once selected, you won't be able to change it.");
        FormText introLabel = ft.createFormText(parent, introText, false);
        introLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Alert label.
        final FormText alertLabel = ft.createFormText(parent, "", true);
        alertLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Label
        String computerNameLabelText = "<b>" + _("Provide a repository name") + "</b>";
        FormText computerNameLabel = ft.createFormText(parent, computerNameLabelText, false);
        computerNameLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // Computer name
        final Text computerNameText = ft.createText(parent, "", SWT.BORDER);
        computerNameText.setLayoutData(new TableWrapData(TableWrapData.FILL));
        computerNameText.setMessage(_("Repository name"));
        computerNameText.setText(Compat.COMPUTER_NAME);
        computerNameText.setFocus();

        // Sign in button
        final Button linkButton = ft.createButton(parent, _("Link"), SWT.PUSH);
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

        ((TableWrapLayout) parent.getLayout()).numColumns = 1;

        // App name
        Label appnameLabel = ft.createAppnameLabel(parent, _("Minarca"), SWT.CENTER);
        appnameLabel.setLayoutData(new TableWrapData(TableWrapData.FILL));

        // App icon
        Label icon = this.ft.createLabel(parent, null);
        icon.setImage(JFaceResources.getImage(Images.MINARCA_128_PNG));
        icon.setLayoutData(new TableWrapData(TableWrapData.CENTER));

        // Introduction message
        String introText = "<h2>" + _("Success !") + "</h2><br/>";
        introText += _("Your system is now configure to backup it self once a day with Minarca!");
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
        return getShell().computeSize(681, 519, true);
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
            return _("Repository name cannot be empty.");
        }
        LOGGER.info("link computer {}", name);
        try {
            API.instance().link(name, this.client, force);
        } catch (RepositoryNameAlreadyInUseException e) {
            final MutableInt returnCode = new MutableInt();
            Display.getDefault().syncExec(new Runnable() {
                @Override
                public void run() {
                    int r = DetailMessageDialog.openYesNoQuestion(
                            getShell(),
                            Display.getAppName(),
                            _("Are you sure you want to keep the given repository name ?"),
                            _("The given repository name is already in use in Minarca. "
                                    + "You may keep this repository name if the name is "
                                    + "no longer used by another system currently "
                                    + "link to Minarca."),
                            null).getReturnCode();
                    returnCode.setValue(r);
                }
            });
            if (returnCode.intValue() == IDialogConstants.YES_ID) {
                // Force usage of the computer name
                return handleLinkComputer(name, true);
            }
            return _("Change the repository name");
        } catch (APIException e) {
            LOGGER.warn("fail to register computer", e);
            return e.getMessage();
        } catch (IllegalArgumentException e) {
            LOGGER.warn("invalid computername: " + name, e);
            return _("Should only contains letters, numbers, dash (-) and dot (.)");
        } catch (IOException e) {
            LOGGER.warn("fail to register computer", e);
            return _("<strong>Communication error!</strong> Check if you can connected to Internet.");
        } catch (Exception e) {
            LOGGER.warn("fail to register computer", e);
            return _("<strong>Unknown error occurred!</strong> If the problem persists, try to re-install Minarca.");
        }

        return null;
    }

    /**
     * Called to handle user sign in.
     * <p>
     * This implementation will establish a connection via HTTP and or SSH to make sure the connection and credentials
     * are valid.
     * 
     * @param remoteserver
     *            the remote server address.
     * @param username
     *            the username for authentication
     * @param password
     *            the password for authentication.
     * @return an error message or null if OK.
     */
    protected boolean handleSignIn(String remoteserver, String username, String password) {
        Validate.notBlank(remoteserver);
        Validate.notBlank(username);
        Validate.notBlank(password);
        // Add http if not provided.
        if (!(remoteserver.startsWith("http://") || remoteserver.startsWith("https://"))) {
            remoteserver = "http://" + remoteserver;
        }
        // Try to establish communication with HTTP first.
        LOGGER.info("sign in as [{}]", username);
        try {
            this.client = API.instance().connect(remoteserver, username, password);
        } catch (APIException e) {
            LOGGER.warn("fail to authenticate", e);
            DetailMessageDialog.openWarning(getShell(), Display.getAppName(), _("Fail to authenticate with the server"), e.getMessage(), e);
            return false;
        }
        return true;
    }

}
