package com.patrikdufresne.minarca.ui;

import static com.patrikdufresne.minarca.Localized._;

import java.util.Calendar;

import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.SelectionAdapter;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.graphics.Image;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.program.Program;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Link;
import org.eclipse.swt.widgets.Shell;

import com.patrikdufresne.minarca.Main;

/**
 * Reusable composite to show About information.
 * 
 * @author Patrik Dufresne
 * 
 */
public class AboutDialog extends Dialog {

    /**
     * Create a new About dialog.
     * 
     * @param shell
     *            the parent of this dialog.
     */
    public AboutDialog(Shell shell) {
        super(shell);
    }

    /**
     * This implementation close the dialog.
     * 
     * @see org.eclipse.jface.dialogs.Dialog#buttonPressed(int)
     */
    @Override
    protected void buttonPressed(int buttonId) {
        cancelPressed();
    }

    /**
     * This implementation set the windows title
     */
    @Override
    protected void configureShell(Shell newShell) {
        super.configureShell(newShell);
        newShell.setText(_("About {0}", Display.getAppName()));
    }

    /**
     * This implementation create a close button.
     * 
     * @see org.eclipse.jface.dialogs.Dialog#createButtonsForButtonBar(org.eclipse.swt.widgets.Composite)
     */
    @Override
    protected void createButtonsForButtonBar(Composite parent) {
        createButton(parent, IDialogConstants.CLOSE_ID, IDialogConstants.CLOSE_LABEL, true);
    }

    /**
     * This implementation create the content of the about dialog.
     * 
     * @see org.eclipse.jface.dialogs.Dialog#createDialogArea(org.eclipse.swt.widgets.Composite)
     */
    @Override
    protected Control createDialogArea(Composite parent) {

        // Create the composite to hold all the controls
        Composite comp = (Composite) super.createDialogArea(parent);

        // Image
        Image applicationIcon = JFaceResources.getImage(Images.MINARCA_128_PNG);
        Label imageLabel = new Label(comp, SWT.NONE);
        imageLabel.setImage(applicationIcon);
        imageLabel.setLayoutData(new GridData(SWT.CENTER, SWT.FILL, true, false));

        // App name and version
        String appName = Display.getAppName();
        String version = Display.getAppVersion();
        if (version != null) {
            appName += " " + version;
        }
        Label appNameText = new Label(comp, SWT.CENTER);
        appNameText.setText(appName);
        appNameText.setFont(JFaceResources.getFont(JFaceResources.HEADER_FONT));
        appNameText.setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, false));
        appNameText.setBackground(this.getShell().getBackground());

        // App description
        String appDescription = _("Minarca is an all integrated online backup solution.");
        Label appDescText = new Label(comp, SWT.CENTER);
        appDescText.setText(appDescription);
        appDescText.setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, false));
        appDescText.setBackground(this.getShell().getBackground());

        // App copyright
        Label appCopyrightText = new Label(comp, SWT.CENTER);
        appCopyrightText.setText(Main.getCopyrightText());
        appCopyrightText.setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, false));
        appCopyrightText.setBackground(this.getShell().getBackground());

        // Application web site
        Link appWebSite = new Link(comp, SWT.NONE);
        appWebSite.setText("<a>Minarca (http://minarca.info/)</a>"); //$NON-NLS-1$ //$NON-NLS-2$
        appWebSite.setLayoutData(new GridData(SWT.CENTER, SWT.FILL, true, false));
        appWebSite.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent event) {
                Program.launch("http://minarca.info/");
            }
        });

        return comp;
    }
}
