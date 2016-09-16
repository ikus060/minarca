package com.patrikdufresne.minarca.ui;

import static com.patrikdufresne.minarca.Localized._;

import java.io.File;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import org.apache.commons.io.FilenameUtils;
import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.layout.GridLayoutFactory;
import org.eclipse.swt.SWT;
import org.eclipse.swt.custom.ScrolledComposite;
import org.eclipse.swt.events.SelectionAdapter;
import org.eclipse.swt.events.SelectionEvent;
import org.eclipse.swt.graphics.Point;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Button;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.DirectoryDialog;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.FileDialog;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Shell;

import com.patrikdufresne.minarca.core.GlobPattern;
import com.patrikdufresne.minarca.core.internal.Compat;
import com.patrikdufresne.switchbutton.SwitchButton;

/**
 * Selective backup dialog used to manage the pattern rules.
 * 
 * @author Patrik Dufresne
 * 
 */
public class SelectiveDialog extends Dialog {

    private static final int PATH_MAX_LENGTH = 50;

    /**
     * Number of pixel to free (to avoid filling all the screen).
     */
    private static final int WINDOW_HEIGHT_PADDING = 55;

    private CList customList;

    private List<GlobPattern> patterns = new ArrayList<GlobPattern>();

    /**
     * True to show all advance patterns.
     */
    private boolean showAdvance = false;

    protected SelectiveDialog(Shell parentShell) {
        super(parentShell);
    }

    /**
     * Sets dialog title
     */
    @Override
    protected void configureShell(Shell newShell) {
        super.configureShell(newShell);
        newShell.setText(_("Selective backup"));
    }

    /**
     * Override creation of button bar to add Advance button.
     */
    @Override
    protected Control createButtonBar(Composite parent) {
        Composite composite = new Composite(parent, SWT.NONE);
        GridLayout layout = new GridLayout();
        layout.marginWidth = 0;
        layout.marginHeight = 0;
        layout.horizontalSpacing = 0;
        composite.setLayout(layout);
        composite.setLayoutData(new GridData(SWT.FILL, SWT.CENTER, false, false));
        composite.setFont(parent.getFont());

        // Continue with default creation of button.
        Control buttonSection = super.createButtonBar(composite);
        ((GridData) buttonSection.getLayoutData()).grabExcessHorizontalSpace = true;
        return composite;
    }

    @Override
    protected Control createDialogArea(Composite parent) {

        Composite comp = (Composite) super.createDialogArea(parent);

        // Top label
        Label label = new Label(comp, SWT.WRAP);
        label.setText(_("Select files or folders you want to include or exclude from your backup."));
        label.setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, false));
        Point labelSize = label.computeSize(SWT.DEFAULT, SWT.DEFAULT);
        ((GridData) label.getLayoutData()).widthHint = (int) (labelSize.x * 0.85f);

        // Create a scrolled composite for the list.
        ScrolledComposite scrollable = new ScrolledComposite(comp, SWT.BORDER | SWT.V_SCROLL);
        scrollable.setExpandHorizontal(true);
        scrollable.setExpandVertical(true);
        scrollable.setMinWidth(0);
        scrollable.setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, false));

        // Create the custom list inside the scrolled composite.
        customList = new CList(scrollable, SWT.NONE);

        // Create custom include / exclude.
        refreshCustomList(false);
        scrollable.setContent(customList);

        Composite buttons = new Composite(comp, SWT.NONE);
        GridLayoutFactory.fillDefaults().numColumns(3).applyTo(buttons);

        // Add folder button
        Button addFolderButton = new Button(buttons, SWT.PUSH);
        addFolderButton.setText(_("Add folder..."));
        addFolderButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleAddFolderCustom();
            }
        });

        Button addFileButton = new Button(buttons, SWT.PUSH);
        addFileButton.setText(_("Add file..."));
        addFileButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleAddFileCustom();
            }
        });

        final Button showAdvanceButton = new Button(buttons, SWT.CHECK);
        showAdvanceButton.setText(_("Show advance patterns"));
        showAdvanceButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleShowAdvancePatterns(showAdvanceButton.getSelection());
            }
        });

        return comp;

    }

    /**
     * Create the necessary component to represent a single predefined filter.
     * 
     * @param parent
     *            the parent
     * @param label
     *            the label (translated)
     * @param pattern
     *            the globing pattern
     */
    private void createItem(CList parent, final GlobPattern pattern) {
        // Create separator (if required)
        if (parent.getChildren().length > 0) {
            new Label(parent, SWT.SEPARATOR | SWT.HORIZONTAL);
        }
        // Define label
        String label;
        if (pattern.isGlobbing()) {
            label = _("Custom pattern");
        } else {
            label = FilenameUtils.getBaseName(pattern.value());
            if (!pattern.isFileExists()) {
                label += " " + _("(not exists)");
            }
        }
        // Create an item.
        CListItem item = new CListItem(parent, label);
        SwitchButton button = item.createSwitchButton();
        button.setToolTipText(_("Include / Exclude"));
        button.setSelection(pattern.isInclude());
        button.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleToggleSwitch(e, pattern);
            }
        });

        // Update the item labels
        String helptext = pattern.toString();
        item.setToolTipText(helptext);
        if (helptext.length() > PATH_MAX_LENGTH) {
            item.setTitleHelpText(helptext.substring(0, PATH_MAX_LENGTH) + Dialog.ELLIPSIS);
        } else {
            item.setTitleHelpText(helptext.toString());
        }

        // Create Delete button if required.
        Button deleteButton = item.createButtonDelete();
        deleteButton.setToolTipText(_("Delete"));
        deleteButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleDelete(pattern);
            }
        });

    }

    /**
     * Return the include patterns selected by the user
     * 
     * @return
     */
    public List<GlobPattern> getPatterns() {
        return new ArrayList<GlobPattern>(this.patterns);
    }

    /**
     * Called when the user click the "Add file" button.
     */
    protected void handleAddFileCustom() {
        // Open a dialog to select a folder or a file.
        FileDialog dlg = new FileDialog(getShell(), SWT.OPEN | SWT.MULTI);
        dlg.setText(getShell().getText());
        // Open dialog and check return code.
        if (dlg.open() == null) {
            // Cancel by user
            return;
        }
        // Add selected files as include patterns
        String folder = dlg.getFilterPath();
        String[] files = dlg.getFileNames();
        for (String file : files) {
            handleAddFolderOrFile(new File(folder, file));
        }
        // Update the view.
        refreshCustomList(true);
    }

    /**
     * Called when the user click the "Add Folder" button to add a new item.
     */
    protected void handleAddFolderCustom() {

        // Open a dialog to select a folder or a file.
        DirectoryDialog dlg = new DirectoryDialog(getShell(), SWT.NONE);
        dlg.setText(getShell().getText());
        dlg.setMessage(_("Select a folder to be added to your selective backup."));
        // Set default location to "Home".
        dlg.setFilterPath(Compat.HOME);
        // Open dialog and check return code.
        if (dlg.open() == null) {
            // Cancel by user
            return;
        }
        // Get the selection from the dialog
        String file = dlg.getFilterPath();
        handleAddFolderOrFile(new File(file));

        // Update the view.
        refreshCustomList(true);
    }

    /**
     * Called to add a new file or folder to the pattern list.
     * 
     * @param file
     */
    protected void handleAddFolderOrFile(File file) {
        // Check if file exists
        GlobPattern p = new GlobPattern(true, file);
        if (!p.isFileExists()) {
            DetailMessageDialog.openInformation(
                    getShell(),
                    getShell().getText(),
                    _("Selected item doesn't exists!"),
                    _("The path `{0}` cannot be include because it doesn't exists.", file));
            return;
        }

        // Check if modification required.
        if (patterns.contains(p)) {
            DetailMessageDialog.openInformation(
                    getShell(),
                    getShell().getText(),
                    _("Selected item is already include!"),
                    _("The path `{0}` is already include in you selective backup.", file));
            return;
        }

        // Check if selected item is already excluded
        boolean excluded = false;
        for (GlobPattern e : this.patterns) {
            if (!e.isInclude() && e.matches(file)) {
                excluded = true;
            }
        }
        if (excluded) {
            DetailMessageDialog.openWarning(
                    getShell(),
                    getShell().getText(),
                    _("Selected item is excluded by another pattern."),
                    _("The path `{0}` is currently excluded by another pattern. You may need to reorganize your patterns to properly include the selected item.", file));
        }

        // Check if predefined.
        patterns.add(p);
    }

    /**
     * Called when the user click the "delete" button.
     * 
     * @param event
     * @param list
     */
    protected void handleDelete(GlobPattern pattern) {
        patterns.remove(pattern);
        refreshCustomList(true);
    }

    /**
     * Called when user click on "show advance" check box.
     * 
     * @param selection
     */
    protected void handleShowAdvancePatterns(boolean selection) {
        this.showAdvance = selection;
        refreshCustomList(true);
    }

    /**
     * Called when the user click the toggle button.
     * 
     * @param event
     * @param list
     */
    protected void handleToggleSwitch(SelectionEvent event, GlobPattern pattern) {
        patterns.remove(pattern);
        boolean selection = !((SwitchButton) event.widget).getSelection();
        patterns.add(new GlobPattern(selection, pattern.value()));
    }

    /**
     * Refresh the custom list of include / exclude.
     */
    private void refreshCustomList(boolean relayout) {
        // Dispose previous widget.
        for (Control child : this.customList.getChildren()) {
            child.dispose();
        }

        // Compute the custom list of includes
        for (GlobPattern p : getPatterns()) {
            if (!GlobPattern.isAdvance(p) || this.showAdvance) {
                createItem(this.customList, p);
            }
        }

        // Create empty item is required
        if (this.customList.getChildren().length == 0) {
            new CListItem(this.customList);
        }

        /*
         * Relayout scrollable.
         */
        // Compute the maximum size so the dialog is render in the screen.
        int windowHeight = getShell().getBounds().height;
        int widgetHeight = this.customList.getParent().getSize().y;
        int monitorHeight = Display.getDefault().getBounds().height;
        int maxHeight = monitorHeight - windowHeight + widgetHeight - WINDOW_HEIGHT_PADDING;

        // Compute the widget size
        Point size = customList.computeSize(SWT.DEFAULT, SWT.DEFAULT);

        // Fix the scrollable size
        ScrolledComposite scrollable = (ScrolledComposite) this.customList.getParent();
        scrollable.setMinHeight(size.y);
        ((GridData) scrollable.getLayoutData()).widthHint = size.x;
        ((GridData) scrollable.getLayoutData()).heightHint = Math.min(size.y, maxHeight);

        if (relayout) {
            // Recompute the dialog size.
            getShell().layout(true, true);
            getShell().setSize(getShell().computeSize(SWT.DEFAULT, SWT.DEFAULT));
        }
    }

    /**
     * Initialise the patterns.
     * 
     * @param patterns
     */
    public void setPatterns(Collection<GlobPattern> patterns) {
        this.patterns = new ArrayList<GlobPattern>(patterns);
    }

}
