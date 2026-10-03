package com.manutencaonamao.app;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.WebChromeClient;
import android.webkit.ValueCallback;
import android.webkit.PermissionRequest;
import android.net.Uri;
import android.content.Intent;
import android.os.Environment;
import java.io.File;
import android.provider.MediaStore;
import android.content.Context;
import android.content.ContentValues;
import android.webkit.JavascriptInterface;
import java.util.ArrayList;
import java.io.OutputStream;
import android.util.Base64;
import android.content.ActivityNotFoundException;

public class MainActivity extends Activity {
    private ValueCallback<Uri[]> uploadMessage;
    private final static int FILECHOOSER_RESULTCODE = 1;
    private Uri mCapturedImageURI = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        
        android.os.StrictMode.VmPolicy.Builder builder = new android.os.StrictMode.VmPolicy.Builder();
        android.os.StrictMode.setVmPolicy(builder.build());
        
        WebView webView = new WebView(this);
        WebSettings webSettings = webView.getSettings();
        webSettings.setDefaultTextEncodingName("utf-8");
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setAllowFileAccess(true);
        webSettings.setAllowFileAccessFromFileURLs(true);
        webSettings.setAllowUniversalAccessFromFileURLs(true);
        webSettings.setDatabaseEnabled(true);
        webSettings.setMediaPlaybackRequiresUserGesture(false);
        
        webView.addJavascriptInterface(new WebAppInterface(this), "AndroidApp");
        
        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("file://")) {
                    return false;
                }
                try {
                    Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                    view.getContext().startActivity(intent);
                    return true;
                } catch (Exception e) {
                    return true;
                }
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(final PermissionRequest request) {
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        request.grant(request.getResources());
                    }
                });
            }

            @Override
            public boolean onJsAlert(WebView view, String url, String message, final android.webkit.JsResult result) {
                new android.app.AlertDialog.Builder(view.getContext())
                    .setTitle("Manuten\u00e7\u00e3o na m\u00e3o")
                    .setMessage(message)
                    .setPositiveButton(android.R.string.ok, new android.content.DialogInterface.OnClickListener() {
                        public void onClick(android.content.DialogInterface dialog, int which) {
                            result.confirm();
                        }
                    })
                    .setCancelable(false)
                    .create()
                    .show();
                return true;
            }

            @Override
            public boolean onJsConfirm(WebView view, String url, String message, final android.webkit.JsResult result) {
                new android.app.AlertDialog.Builder(view.getContext())
                    .setTitle("Confirma\u00e7\u00e3o")
                    .setMessage(message)
                    .setPositiveButton(android.R.string.ok, new android.content.DialogInterface.OnClickListener() {
                        public void onClick(android.content.DialogInterface dialog, int which) {
                            result.confirm();
                        }
                    })
                    .setNegativeButton(android.R.string.cancel, new android.content.DialogInterface.OnClickListener() {
                        public void onClick(android.content.DialogInterface dialog, int which) {
                            result.cancel();
                        }
                    })
                    .setCancelable(false)
                    .create()
                    .show();
                return true;
            }

            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, WebChromeClient.FileChooserParams fileChooserParams) {
                if (uploadMessage != null) {
                    uploadMessage.onReceiveValue(null);
                    uploadMessage = null;
                }
                uploadMessage = filePathCallback;

                Intent takePictureIntent = null;
                boolean isCapture = fileChooserParams.isCaptureEnabled();
                String[] acceptTypes = fileChooserParams.getAcceptTypes();
                boolean isVideo = false;
                if (acceptTypes != null) {
                    for (String type : acceptTypes) {
                        if (type != null && type.contains("video")) {
                            isVideo = true;
                            break;
                        }
                    }
                }

                long now = System.currentTimeMillis();
                ContentValues values = new ContentValues();
                if (isVideo) {
                    takePictureIntent = new Intent(MediaStore.ACTION_VIDEO_CAPTURE);
                    values.put(MediaStore.Video.Media.TITLE, "Manutencao_" + now);
                    values.put(MediaStore.Video.Media.MIME_TYPE, "video/mp4");
                    values.put(MediaStore.Video.Media.DATE_ADDED, now / 1000);
                    mCapturedImageURI = getContentResolver().insert(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, values);
                } else {
                    takePictureIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
                    values.put(MediaStore.Images.Media.TITLE, "Manutencao_" + now);
                    values.put(MediaStore.Images.Media.MIME_TYPE, "image/jpeg");
                    values.put(MediaStore.Images.Media.DATE_ADDED, now / 1000);
                    mCapturedImageURI = getContentResolver().insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values);
                }

                if (takePictureIntent != null && mCapturedImageURI != null) {
                    takePictureIntent.putExtra(MediaStore.EXTRA_OUTPUT, mCapturedImageURI);
                }

                if (isCapture && takePictureIntent != null) {
                    try {
                        startActivityForResult(takePictureIntent, FILECHOOSER_RESULTCODE);
                        return true;
                    } catch (Exception e) {}
                }

                Intent contentSelectionIntent = fileChooserParams.createIntent();
                Intent[] intentArray = (takePictureIntent != null) ? new Intent[]{takePictureIntent} : new Intent[0];

                Intent chooserIntent = new Intent(Intent.ACTION_CHOOSER);
                chooserIntent.putExtra(Intent.EXTRA_INTENT, contentSelectionIntent);
                chooserIntent.putExtra(Intent.EXTRA_TITLE, "Selecionar Arquivo ou C\u00e2mera");
                chooserIntent.putExtra(Intent.EXTRA_INITIAL_INTENTS, intentArray);

                try {
                    startActivityForResult(chooserIntent, FILECHOOSER_RESULTCODE);
                } catch (Exception e) {
                    uploadMessage = null;
                    return false;
                }
                return true;
            }
        });

        webView.loadUrl("file:///android_asset/index.html");
        setContentView(webView);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        if (requestCode == FILECHOOSER_RESULTCODE) {
            if (uploadMessage == null) return;
            Uri[] results = null;
            if (resultCode == Activity.RESULT_OK) {
                if (data == null || data.getData() == null) {
                    if (mCapturedImageURI != null) {
                        results = new Uri[]{mCapturedImageURI};
                    }
                } else {
                    String dataString = data.getDataString();
                    if (data.getClipData() != null) {
                        int count = data.getClipData().getItemCount();
                        results = new Uri[count];
                        for (int i = 0; i < count; i++) {
                            results[i] = data.getClipData().getItemAt(i).getUri();
                        }
                    } else if (dataString != null) {
                        results = new Uri[]{Uri.parse(dataString)};
                    }
                }
            }
            uploadMessage.onReceiveValue(results);
            uploadMessage = null;
        }
    }

    public static class WebAppInterface {
        Context mContext;
        private StringBuilder chunkBuffer = new StringBuilder();
        private ArrayList<Uri> uris = new ArrayList<Uri>();

        WebAppInterface(Context c) { mContext = c; }
        
        @JavascriptInterface
        public String getAppVersion() { return "2.0"; }

        @JavascriptInterface
        public void clearChunkBuffer() {
            chunkBuffer.setLength(0);
        }

        @JavascriptInterface
        public void appendChunk(String chunk) {
            chunkBuffer.append(chunk);
        }

        @JavascriptInterface
        public void clearShares() {
            uris.clear();
        }

        @JavascriptInterface
        public void addShareFileFromChunks(String filename) {
            String base64Data = chunkBuffer.toString();
            chunkBuffer.setLength(0);
            addShareFile(filename, base64Data);
        }

        @JavascriptInterface
        public void addShareFile(String filename, String base64Data) {
            try {
                String base64Image = base64Data;
                int commaIndex = base64Data.indexOf(",");
                if (commaIndex != -1) {
                    base64Image = base64Data.substring(commaIndex + 1);
                }
                byte[] decodedString = Base64.decode(base64Image, Base64.DEFAULT);
                
                ContentValues values = new ContentValues();
                values.put(MediaStore.MediaColumns.DISPLAY_NAME, filename);
                values.put(MediaStore.MediaColumns.MIME_TYPE, filename.toLowerCase().endsWith(".mp4") ? "video/mp4" : "image/jpeg");
                
                Uri external = filename.toLowerCase().endsWith(".mp4") ? MediaStore.Video.Media.EXTERNAL_CONTENT_URI : MediaStore.Images.Media.EXTERNAL_CONTENT_URI;
                Uri uri = mContext.getContentResolver().insert(external, values);
                
                if (uri != null) {
                    OutputStream os = mContext.getContentResolver().openOutputStream(uri);
                    os.write(decodedString);
                    os.flush();
                    os.close();
                    uris.add(uri);
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

        @JavascriptInterface
        public void commitShare(String text) {
            if (uris.size() == 0 && (text == null || text.isEmpty())) return;
            
            Intent shareIntent = new Intent();
            if (uris.size() == 1) {
                shareIntent.setAction(Intent.ACTION_SEND);
                shareIntent.putExtra(Intent.EXTRA_STREAM, uris.get(0));
            } else if (uris.size() > 1) {
                shareIntent.setAction(Intent.ACTION_SEND_MULTIPLE);
                shareIntent.putParcelableArrayListExtra(Intent.EXTRA_STREAM, uris);
            } else {
                shareIntent.setAction(Intent.ACTION_SEND);
            }
            
            shareIntent.setType(uris.size() > 0 ? (uris.get(0).toString().contains("video") ? "video/*" : "image/*") : "text/plain");
            shareIntent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            if (text != null && !text.isEmpty()) {
                shareIntent.putExtra(Intent.EXTRA_TEXT, text);
            }
            shareIntent.setPackage("com.whatsapp");
            
            try {
                mContext.startActivity(shareIntent);
            } catch (ActivityNotFoundException ex) {
                shareIntent.setPackage(null);
                mContext.startActivity(Intent.createChooser(shareIntent, "Compartilhar com"));
            }
        }
    }
}
