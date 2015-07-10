package com.patrikdufresne.minarca.ui;

import static com.patrikdufresne.minarca.Localized._;
import static com.patrikdufresne.minarca.core.GlobPattern.getDocumentsPatterns;
import static com.patrikdufresne.minarca.core.GlobPattern.getDownloadsPatterns;
import static com.patrikdufresne.minarca.core.GlobPattern.getMusicPatterns;
import static com.patrikdufresne.minarca.core.GlobPattern.getOsPatterns;
import static com.patrikdufresne.minarca.core.GlobPattern.getPicturesPatterns;
import static com.patrikdufresne.minarca.core.GlobPattern.getVideosPatterns;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

import org.apache.commons.io.FilenameUtils;
import org.apache.commons.lang3.StringUtils;
import org.eclipse.jface.dialogs.Dialog;
import org.eclipse.jface.dialogs.IDialogConstants;
import org.eclipse.jface.layout.GridLayoutFactory;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.jface.window.Window;
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
import org.eclipse.swt.widgets.FileDialog;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Shell;

import com.patrikdufresne.minarca.core.GlobPattern;
import com.patrikdufresne.switchbutton.SwitchButton;

/**
 * Selective backup dialog used to manage the include and exclude rules.
 * 
 * @author Patrik Dufresne
 * 
 */
public class SelectiveDialog extends Dialog {

    private static final String COMMA = ", ";

    private static final int PATH_MAX_LENGTH = 50;

    /**
     * Return collection of predefined patterns.
     * 
     * @return
     */
    private static List<List<GlobPattern>> getPredefined() {
        return Arrays.asList(getDocumentsPatterns(), getDownloadsPatterns(), getMusicPatterns(), getPicturesPatterns(), getVideosPatterns(), getOsPatterns());
    }

    private CList customList;

    private Set<GlobPattern> excludes = new LinkedHashSet<GlobPattern>();

    private Set<GlobPattern> includes = new LinkedHashSet<GlobPattern>();

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

        // Create advance button.
        Button advanceButton = new Button(composite, SWT.PUSH);
        advanceButton.setText(_("Advance..."));
        ((GridLayout) composite.getLayout()).numColumns++;
        setButtonLayoutData(advanceButton);
        // advanceButton.setLayoutData(new GridData(GridData.HORIZONTAL_ALIGN_CENTER));
        advanceButton.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handleAdvancePatterns();
            }
        });
        ((GridData) advanceButton.getLayoutData()).horizontalIndent = convertHorizontalDLUsToPixels(IDialogConstants.HORIZONTAL_MARGIN);

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

        // Predefine label
        Label predefineLabel = new Label(comp, SWT.NONE);
        predefineLabel.setFont(AppFormToolkit.getFontBold(JFaceResources.DEFAULT_FONT));
        predefineLabel.setText(_("Predefined"));

        CList predefineList = new CList(comp, SWT.BORDER);
        predefineList.setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, false));

        // Create predefine include exclude
        createItem(predefineList, _("Documents"), GlobPattern.getDocumentsPatterns(), true);
        createItem(predefineList, _("Pictures"), GlobPattern.getPicturesPatterns(), true);
        createItem(predefineList, _("Music"), GlobPattern.getMusicPatterns(), true);
        createItem(predefineList, _("Videos"), GlobPattern.getVideosPatterns(), true);
        createItem(predefineList, _("Downloads"), GlobPattern.getDownloadsPatterns(), true);
        createItem(predefineList, _("System files"), GlobPattern.getOsPatterns(), true);

        // Custom Label
        Label customLabel = new Label(comp, SWT.NONE);
        customLabel.setFont(AppFormToolkit.getFontBold(JFaceResources.DEFAULT_FONT));
        customLabel.setText(_("Custom"));

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
        GridLayoutFactory.fillDefaults().numColumns(2).applyTo(buttons);

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

        return comp;

    }

    /**
     * Create the necessary component to represent a single predefined filter.
     * 
     * @param parent
     *            the parent
     * @param label
     *            the label (translated)
     * @param patterns
     *            the list of glob pattern
     * @param predefined
     *            True if creating a predefined item.
     */
    private void createItem(CList parent, String label, final List<GlobPattern> patterns, final boolean predefined) {
        // Create separator (if required)
        if (parent.getChildren().length > 0) {
            new Label(parent, SWT.SEPARATOR | SWT.HORIZONTAL);
        }
        // Create an item.
        CListItem item = new CListItem(parent, label);
        SwitchButton button = item.createSwitchButton();
        button.addSelectionListener(new SelectionAdapter() {
            @Override
            public void widgetSelected(SelectionEvent e) {
                handlePredefine(e, patterns);
            }
        });

        // Check if the patterns matches something.
        List<GlobPattern> matches = new ArrayList<GlobPattern>();
        for (GlobPattern p : patterns) {
            // Don't expend globing (it's too expensive)
            if (p.isGlobbing() || new File(p.value()).exists()) {
                matches.add(p);
            }
        }

        // Update the item labels
        String helptext;
        if (matches.size() > 0) {
            helptext = StringUtils.join(matches, COMMA);
        } else if (!predefined) {
            helptext = StringUtils.join(patterns, COMMA);
        } else {
            helptext = _("No file or folder matching predefined patterns");
        }
        if (helptext.length() > PATH_MAX_LENGTH) {
            item.setTitleHelpText(helptext.substring(0, PATH_MAX_LENGTH) + Dialog.ELLIPSIS);
            item.setToolTipText(StringUtils.join(matches, "\n"));
        } else {
            item.setTitleHelpText(helptext.toString());
            item.setToolTipText(helptext);
        }

        // If the glob pattern doesn't match any thing, disable it.
        item.setEnabled(matches.size() > 0 || !predefined);

        // Check if pattern is selected.
        boolean selected = includes.containsAll(patterns) && Collections.disjoint(excludes, patterns);
        button.setSelection(selected);

        // Create Delete button if required.
        if (!predefined) {

            Button deleteButton = item.createButtonDelete();
            deleteButton.setToolTipText(_("Delete"));
            deleteButton.addSelectionListener(new SelectionAdapter() {
                @Override
                public void widgetSelected(SelectionEvent e) {
                    handleDelete(e, patterns);
                }
            });
        }

    }

    /**
     * Return filtered list of custom exclude patterns.
     * 
     * @return
     */
    private Collection<GlobPattern> getCustomExcludes() {
        Set<GlobPattern> patterns = new HashSet<GlobPattern>(excludes);
        for (Collection<GlobPattern> p : getPredefined()) {
            if (excludes.containsAll(p)) {
                patterns.removeAll(p);
            }
        }
        return patterns;
    }

    /**
     * Return filtered list of custom include patterns.
     * 
     * @return
     */
    private Collection<GlobPattern> getCustomIncludes() {
        Set<GlobPattern> patterns = new HashSet<GlobPattern>(includes);
        for (Collection<GlobPattern> p : getPredefined()) {
            if (includes.containsAll(p)) {
                patterns.removeAll(p);
            }
        }
        return patterns;
    }

    /**
     * Return the exclude pattern selected by the user.
     * 
     * @return
     */
    public List<GlobPattern> getExcludes() {
        return new ArrayList<GlobPattern>(this.excludes);
    }

    /**
     * Return the include patterns selected by the user
     * 
     * @return
     */
    public List<GlobPattern> getIncludes() {
        return new ArrayList<GlobPattern>(this.includes);
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
            if (new File(folder, file).exists()) {
                includes.add(new GlobPattern(new File(folder, file)));
            }
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
        // Open dialog and check return code.
        if (dlg.open() == null) {
            // Cancel by user
            return;
        }
        // Get the selection from the dialog
        String file = dlg.getFilterPath();

        // Check if file exists
        if (!new File(file).exists()) {
            DetailMessageDialog.openInformation(
                    getShell(),
                    getShell().getText(),
                    _("Selected folder doesn't exists!"),
                    _("The folder `{0}` cannot be include because it doesn't exists.", file));
            return;
        }

        // Check if modification required.
        GlobPattern p = new GlobPattern(file);
        if (includes.contains(p)) {
            DetailMessageDialog.openInformation(
                    getShell(),
                    getShell().getText(),
                    _("Selected folder is already include!"),
                    _("The folder `{0}` is already include in you selective backup.", file));
            return;
        }
        // Check if predefined.
        includes.add(p);
        excludes.remove(p);

        // Update the view.
        refreshCustomList(true);
    }

    /**
     * Called when user want to select advance filter.
     */
    protected void handleAdvancePatterns() {
        // Open a dialog to edit filters.
        IncludesDialog dlg = new IncludesDialog(this.getShell());
        dlg.setIncludes(includes);
        dlg.setExcludes(excludes);
        dlg.setPredefinedIncludes(getPredefinedIncludes());
        dlg.setPredefinedExcludes(getPredefinedExcludes());
        if (dlg.open() != Window.OK) {
            return;
        }
        // Update our patterns according to the dialogs data.
        includes = new LinkedHashSet<GlobPattern>(dlg.getIncludes());
        excludes = new LinkedHashSet<GlobPattern>(dlg.getExcludes());

        // Refresh custom section
        refreshCustomList(true);
    }

    /**
     * Return collection of predefined excludes pattern.
     * 
     * @return
     */
    private Collection<GlobPattern> getPredefinedExcludes() {
        Set<GlobPattern> patterns = new HashSet<GlobPattern>();
        for (Collection<GlobPattern> p : getPredefined()) {
            if (excludes.containsAll(p)) {
                patterns.addAll(p);
            }
        }
        return patterns;
    }

    /**
     * Return collection of predefined includes pattern.
     * 
     * @return
     */
    private Collection<GlobPattern> getPredefinedIncludes() {
        Set<GlobPattern> patterns = new HashSet<GlobPattern>();
        for (Collection<GlobPattern> p : getPredefined()) {
            if (includes.containsAll(p)) {
                patterns.addAll(p);
            }
        }
        return patterns;
    }

    /**
     * Called when the user click the "delete" button.
     * 
     * @param event
     * @param list
     */
    protected void handleDelete(SelectionEvent event, List<GlobPattern> list) {
        includes.removeAll(list);
        excludes.removeAll(list);
        refreshCustomList(true);
    }

    /**
     * Cakked when the user click the toggle button.
     * 
     * @param event
     * @param list
     */
    protected void handlePredefine(SelectionEvent event, List<GlobPattern> list) {
        boolean selection = !((SwitchButton) event.widget).getSelection();
        if (selection) {
            includes.addAll(list);
            excludes.removeAll(list);
        } else {
            includes.removeAll(list);
            excludes.addAll(list);
        }
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
        for (GlobPattern p : getCustomIncludes()) {
            String label;
            if (new File(p.value()).exists()) {
                label = FilenameUtils.getBaseName(p.value());
            } else {
                label = _("Custom pattern");
            }
            createItem(this.customList, label, Arrays.asList(p), false);
        }

        // Compute the custom list of exclude
        for (GlobPattern p : getCustomExcludes()) {
            String label;
            if (new File(p.value()).exists()) {
                label = FilenameUtils.getBaseName(p.value());
            } else {
                label = _("Custom pattern");
            }
            createItem(this.customList, label, Arrays.asList(p), false);
        }

        // Create empty item is required
        if (this.customList.getChildren().length == 0) {
            new CListItem(this.customList);
        }

        // Relayout scrollable.
        Point size = customList.computeSize(SWT.DEFAULT, SWT.DEFAULT);
        ScrolledComposite scrollable = (ScrolledComposite) this.customList.getParent();
        scrollable.setMinHeight(size.y);
        ((GridData) scrollable.getLayoutData()).widthHint = size.x;
        ((GridData) scrollable.getLayoutData()).heightHint = Math.min(size.y, 250);

        if (relayout) {
            // Recompute the dialog size.
            getShell().layout(true, true);
            getShell().setSize(getShell().computeSize(SWT.DEFAULT, SWT.DEFAULT));
        }
    }

    /**
     * Initialise the exclude patterns.
     * 
     * @param excludes
     */
    public void setExcludes(Collection<GlobPattern> excludes) {
        this.excludes = new LinkedHashSet<GlobPattern>(excludes);
    }

    /**
     * Initialise the includes patterns.
     * 
     * @param includes
     */
    public void setIncludes(Collection<GlobPattern> includes) {
        this.includes = new LinkedHashSet<GlobPattern>(includes);
    }

}
