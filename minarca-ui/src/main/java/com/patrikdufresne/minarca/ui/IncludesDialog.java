package com.patrikdufresne.minarca.ui;

import static com.patrikdufresne.minarca.Localized._;

import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.awt.image.DirectColorModel;
import java.awt.image.IndexColorModel;
import java.awt.image.WritableRaster;
import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import javax.swing.ImageIcon;
import javax.swing.filechooser.FileSystemView;

import org.eclipse.jface.dialogs.TrayDialog;
import org.eclipse.jface.resource.ImageRegistry;
import org.eclipse.jface.resource.JFaceResources;
import org.eclipse.jface.viewers.CheckStateChangedEvent;
import org.eclipse.jface.viewers.CheckboxTreeViewer;
import org.eclipse.jface.viewers.IBaseLabelProvider;
import org.eclipse.jface.viewers.ICheckStateListener;
import org.eclipse.jface.viewers.ICheckStateProvider;
import org.eclipse.jface.viewers.ITreeContentProvider;
import org.eclipse.jface.viewers.StyledCellLabelProvider;
import org.eclipse.jface.viewers.StyledString;
import org.eclipse.jface.viewers.Viewer;
import org.eclipse.jface.viewers.ViewerCell;
import org.eclipse.swt.SWT;
import org.eclipse.swt.events.DisposeEvent;
import org.eclipse.swt.events.DisposeListener;
import org.eclipse.swt.graphics.Color;
import org.eclipse.swt.graphics.Image;
import org.eclipse.swt.graphics.ImageData;
import org.eclipse.swt.graphics.PaletteData;
import org.eclipse.swt.graphics.Point;
import org.eclipse.swt.graphics.RGB;
import org.eclipse.swt.graphics.TextStyle;
import org.eclipse.swt.layout.GridData;
import org.eclipse.swt.layout.GridLayout;
import org.eclipse.swt.widgets.Composite;
import org.eclipse.swt.widgets.Control;
import org.eclipse.swt.widgets.Display;
import org.eclipse.swt.widgets.Label;
import org.eclipse.swt.widgets.Shell;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.patrikdufresne.minarca.core.API;
import com.patrikdufresne.minarca.core.GlobPattern;

/**
 * Dialog used to display and change includes patterns.
 * 
 * @author ikus060-vm
 *
 */
public class IncludesDialog extends TrayDialog {

	private static final transient Logger LOGGER = LoggerFactory
			.getLogger(IncludesDialog.class);

	private static ImageData convertToSWT(BufferedImage bufferedImage) {
		if (bufferedImage.getColorModel() instanceof DirectColorModel) {
			DirectColorModel colorModel = (DirectColorModel) bufferedImage
					.getColorModel();
			PaletteData palette = new PaletteData(colorModel.getRedMask(),
					colorModel.getGreenMask(), colorModel.getBlueMask());
			ImageData data = new ImageData(bufferedImage.getWidth(),
					bufferedImage.getHeight(), colorModel.getPixelSize(),
					palette);
			for (int y = 0; y < data.height; y++) {
				for (int x = 0; x < data.width; x++) {
					int rgb = bufferedImage.getRGB(x, y);
					int pixel = palette.getPixel(new RGB((rgb >> 16) & 0xFF,
							(rgb >> 8) & 0xFF, rgb & 0xFF));
					data.setPixel(x, y, pixel);
					if (colorModel.hasAlpha()) {
						data.setAlpha(x, y, (rgb >> 24) & 0xFF);
					}
				}
			}
			return data;
		} else if (bufferedImage.getColorModel() instanceof IndexColorModel) {
			IndexColorModel colorModel = (IndexColorModel) bufferedImage
					.getColorModel();
			int size = colorModel.getMapSize();
			byte[] reds = new byte[size];
			byte[] greens = new byte[size];
			byte[] blues = new byte[size];
			colorModel.getReds(reds);
			colorModel.getGreens(greens);
			colorModel.getBlues(blues);
			RGB[] rgbs = new RGB[size];
			for (int i = 0; i < rgbs.length; i++) {
				rgbs[i] = new RGB(reds[i] & 0xFF, greens[i] & 0xFF,
						blues[i] & 0xFF);
			}
			PaletteData palette = new PaletteData(rgbs);
			ImageData data = new ImageData(bufferedImage.getWidth(),
					bufferedImage.getHeight(), colorModel.getPixelSize(),
					palette);
			data.transparentPixel = colorModel.getTransparentPixel();
			WritableRaster raster = bufferedImage.getRaster();
			int[] pixelArray = new int[1];
			for (int y = 0; y < data.height; y++) {
				for (int x = 0; x < data.width; x++) {
					raster.getPixel(x, y, pixelArray);
					data.setPixel(x, y, pixelArray[0]);
				}
			}
			return data;
		}
		return null;
	}

	/**
	 * Used to get an icon to represent the given file.
	 * 
	 * @param file
	 *            the file
	 * @return the image.
	 */
	private static Image createFileIcon(File file) {
		// Use AWT to get icon for file.
		ImageIcon systemIcon = (ImageIcon) FileSystemView.getFileSystemView()
				.getSystemIcon(file);
		if (systemIcon == null) {
			// the system icon may be null...
			return null;
		}
		java.awt.Image image = systemIcon.getImage();
		if (image instanceof BufferedImage) {
			return new Image(Display.getDefault(),
					convertToSWT((BufferedImage) image));
		}
		int width = image.getWidth(null);
		int height = image.getHeight(null);
		BufferedImage bufferedImage = new BufferedImage(width, height,
				BufferedImage.TYPE_INT_ARGB);
		Graphics2D g2d = bufferedImage.createGraphics();
		g2d.drawImage(image, 0, 0, null);
		g2d.dispose();
		return new Image(Display.getDefault(), convertToSWT(bufferedImage));
	}

	private List<GlobPattern> excludes = Collections.emptyList();

	private AppFormToolkit ft;

	private ImageRegistry imageRegistry;

	private List<GlobPattern> includes = Collections.emptyList();

	private CheckboxTreeViewer viewer;

	/**
	 * Default constructor.
	 * 
	 * @param parentShell
	 */
	protected IncludesDialog(Shell parentShell) {
		super(parentShell);
		this.ft = new AppFormToolkit(Display.getCurrent());
	}

	/**
	 * Sets dialog title
	 */
	@Override
	protected void configureShell(Shell newShell) {
		super.configureShell(newShell);
		newShell.setText(_("Change selective backup"));
		newShell.addDisposeListener(new DisposeListener() {
			@Override
			public void widgetDisposed(DisposeEvent e) {
				dispose();
			}
		});
	}

	protected boolean containsInclude(File file) {
		GlobPattern p = new GlobPattern(file.getAbsolutePath());
		for (GlobPattern inc : includes) {
			if (inc.toString().startsWith(p.toString())) {
				return true;
			}
		}
		return false;
	}

	private ICheckStateListener createCheckStateListener() {
		return new ICheckStateListener() {
			@Override
			public void checkStateChanged(CheckStateChangedEvent event) {
				if (!(event.getElement() instanceof File)) {
					return;
				}
				File file = (File) event.getElement();
				if (event.getChecked()) {
					// Add the pattern to include
					include(file);
				} else {
					// Remove the pattern from include
					exclude(file);
				}
				viewer.refresh();
			}
		};
	}

	private ICheckStateProvider createCheckStateProvider() {
		return new ICheckStateProvider() {
			@Override
			public boolean isChecked(Object element) {
				if (!(element instanceof File)) {
					return false;
				}
				return isExcluded((File) element) == null
						&& (isIncluded((File) element) != null || containsInclude((File) element));
			}

			@Override
			public boolean isGrayed(Object element) {
				if (!(element instanceof File)) {
					return false;
				}
				return isIncluded((File) element) == null;
			}
		};
	}

	private ITreeContentProvider createContentProvider() {

		return new ITreeContentProvider() {

			@Override
			public void dispose() {
			}

			@Override
			public Object[] getChildren(Object parentElement) {
				File file = (File) parentElement;
				return file.listFiles();
			}

			@Override
			public Object[] getElements(Object inputElement) {
				return (File[]) inputElement;
			}

			@Override
			public Object getParent(Object element) {
				File file = (File) element;
				return file.getParentFile();
			}

			@Override
			public boolean hasChildren(Object element) {
				File file = (File) element;
				if (file.isDirectory()) {
					return true;
				}
				return false;
			}

			public void inputChanged(Viewer v, Object oldInput, Object newInput) {
			}
		};
	}

	@Override
	protected Control createDialogArea(Composite parent) {
		Composite comp = new Composite(parent, SWT.NONE);
		comp.setLayoutData(new GridData(SWT.FILL, SWT.FILL, true, true));
		comp.setLayout(new GridLayout(1, true));

		// Intro label
		Label label = new Label(comp, SWT.NONE);
		label.setText(_("Select or unselect folder to be backup by minarca."));

		// Tree viewer
		this.viewer = new CheckboxTreeViewer(comp, SWT.H_SCROLL | SWT.V_SCROLL
				| SWT.BORDER | SWT.CHECK);
		this.viewer.setContentProvider(createContentProvider());
		this.viewer.setLabelProvider(createLabelProvider());
		this.viewer.setCheckStateProvider(createCheckStateProvider());
		this.viewer.setInput(new File[] { API.getHomeDrive() });
		this.viewer.getControl().setLayoutData(
				new GridData(SWT.FILL, SWT.FILL, true, true));
		this.viewer.addCheckStateListener(createCheckStateListener());

		return comp;
	}

	/**
	 * Label provide to provide a name and icon to each folder / file.
	 * 
	 * @return
	 */
	private IBaseLabelProvider createLabelProvider() {
		return new StyledCellLabelProvider() {

			StyledString.Styler styler = new StyledString.Styler() {
				@Override
				public void applyStyles(TextStyle textStyle) {
					textStyle.foreground = Display.getCurrent().getSystemColor(
							SWT.COLOR_WIDGET_NORMAL_SHADOW);
					textStyle.font = AppFormToolkit
							.getFontItalic(JFaceResources.DIALOG_FONT);
				}

			};

			/**
			 * Get name of the file or directory.
			 * 
			 * @param file
			 * @return
			 */
			private String getFileName(File file) {
				String name = file.getName();
				return name.isEmpty() ? file.getPath() : name;
			}

			/**
			 * Called to update the viewer cell.
			 */
			@Override
			public void update(ViewerCell cell) {
				Object element = cell.getElement();
				File file = (File) element;
				StyledString text = new StyledString();
				text.append(getFileName(file));
				if (isExcluded(file) != null) {
					text.append(" ");
					text.append(_("(Exclude)"), styler);
				} else if (isIncluded(file) != null) {
					text.append(" ");
					text.append(_("(Include)"), styler);
				}
				cell.setImage(getFileIcon(file));
				cell.setText(text.toString());
				cell.setStyleRanges(text.getStyleRanges());
				super.update(cell);
			}
		};
	}

	/**
	 * Called when the shell associated with this dialog is closed.
	 */
	protected void dispose() {
		// Release the images.
		if (this.imageRegistry != null) {
			this.imageRegistry.dispose();
		}
		if (this.ft != null) {
			this.ft.dispose();
		}
	}

	/**
	 * Called when user uncheck an item.
	 * 
	 * @param file
	 */
	protected void exclude(File file) {
		// Check if the file is included.
		GlobPattern include = isIncluded(file);
		if (include == null) {
			// Nothing to do -- it's not included.
			return;
		}
		// Check if the file is already excluded
		GlobPattern exclude = isExcluded(file);
		if (exclude != null) {
			// Nothing to do -- Already excluded
			return;
		}

		// Need to remove the include pattern
		if (include.equals(new GlobPattern(file))) {
			if (isDefaultInclude(include)) {
				DetailMessageDialog.openWarning(this.getShell(), _("Ignore"),
						_("Can''t ignore the {0} since it''s "
								+ "included by default.", file.toString()),
						_("You are trying to ignore a folder or a file that "
								+ "is included by default. If you really "
								+ "want to ignore this file, change your "
								+ "configuration in 'Selective backup' "
								+ "preferences."));
				return;
			}
			LOGGER.debug("remove include pattern [{}]", include);
			includes.remove(include);
			return;
		}

		// Add an exclude pattern.
		exclude = new GlobPattern(file);
		LOGGER.debug("add exclude pattern [{}]", exclude);
		excludes.add(exclude);

	}

	public List<GlobPattern> getExcludes() {
		return Collections.unmodifiableList(this.excludes);
	}

	/**
	 * Get file icon for the given file. This method used a file registry to
	 * cahed the image and handle disposable of the resources.
	 * 
	 * @param file
	 *            the file
	 * @return the image
	 */
	private Image getFileIcon(File file) {
		// Check if the image is already created and available in image
		// registry.
		if (imageRegistry == null) {
			this.imageRegistry = new ImageRegistry();
		}
		Image image = imageRegistry.get(file.getAbsolutePath());
		if (image != null) {
			return image;
		}
		// Create image since not available.
		image = createFileIcon(file);
		if (image != null) {
			imageRegistry.put(file.getAbsolutePath(), image);
		}
		return image;
	}

	/**
	 * Get the includes patterns.
	 * 
	 * @return
	 */
	public List<GlobPattern> getIncludes() {
		return Collections.unmodifiableList(this.includes);
	}

	/**
	 * Define dialog size.
	 */
	@Override
	protected Point getInitialSize() {
		// Sets fixed window size.
		return new Point(420, 475);
	}

	/**
	 * Called when user check item.
	 * 
	 * @param file
	 */
	protected void include(File file) {
		// Make sure to remove exclude if specific to this file.
		GlobPattern exclude = isExcluded(file);
		if (exclude != null && exclude.equals(new GlobPattern(file))) {
			if (isDefaultExclude(exclude)) {
				DetailMessageDialog.openWarning(this.getShell(), _("Include"),
						_("Can''t include {0} since it''s "
								+ "ignored by default.", file.toString()),
						_("You are trying to include a folder or a file that "
								+ "is ignored by default. If you really "
								+ "want to include this file, change your "
								+ "configuration in 'Selective backup' "
								+ "preferences."));
				return;
			}

			// Need to remove the exclude.
			LOGGER.debug("remove exclude pattern [{}]", exclude);
			this.excludes.remove(exclude);
		}
		// Make sure it's included by something
		GlobPattern include = isIncluded(file);
		if (include == null) {
			// Need to add an include for the given file.
			include = new GlobPattern(file);
			LOGGER.debug("add exclude pattern [{}]", include);
			this.includes.add(include);
		}
	}

	private boolean isDefaultExclude(GlobPattern p) {
		return API.getDefaultExcludes().contains(p);
	}

	private boolean isDefaultInclude(GlobPattern p) {
		return API.getDefaultIncludes().contains(p);
	}

	/**
	 * Check if the given file is excluded.
	 * 
	 * @param file
	 * @return
	 */
	private GlobPattern isExcluded(File file) {
		for (GlobPattern exclude : excludes) {
			if (exclude.matches(file)) {
				return exclude;
			}
		}
		return null;
	}

	/**
	 * Check if the given file is included.
	 * 
	 * @param file
	 * @return
	 */
	private GlobPattern isIncluded(File file) {
		for (GlobPattern include : includes) {
			if (include.matches(file)) {
				return include;
			}
		}
		return null;
	}

	@Override
	protected boolean isResizable() {
		return true;
	}

	public void setExcludes(List<GlobPattern> excludes) {
		this.excludes = new ArrayList<GlobPattern>(excludes);
	}

	/**
	 * Sets the includes patterns
	 * 
	 * @param patterns
	 */
	public void setIncludes(List<GlobPattern> includes) {
		this.includes = new ArrayList<GlobPattern>(includes);
	}
}
