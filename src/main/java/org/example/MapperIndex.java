package org.example;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.net.URI;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.StringTokenizer;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.lib.input.FileSplit;

public class MapperIndex extends Mapper<LongWritable, Text, Text, Text> {
    private Map<String,String> urlMap = new HashMap<>();
    private final Text outKey = new Text();   // the term
    private final Text outVal = new Text();   // the full URL

    @Override
    protected void setup(Context context) throws IOException {

        // load the mapping file from the distributed cache
        URI[] cacheFiles = context.getCacheFiles();
        if (cacheFiles == null) {
            throw new IOException("url_mapping.json not found in Distributed Cache");
        }
        for (URI uri : cacheFiles) {
            // match on the fragment or the filename part
            String frag = uri.getFragment();             // "url_mapping.json"
            String path = uri.getPath();                 // "D:/…/url_mapping_final.json"
            if ("url_mapping.json".equals(frag) || path.endsWith("url_mapping_final.json")) {
                // read straight from the URI’s path
                try (BufferedReader br = new BufferedReader(new FileReader(path))) {
                    Gson gson = new Gson();
                    urlMap = gson.fromJson(
                            br,
                            new TypeToken<Map<String,String>>(){}.getType()
                    );
                }
            }
        }
        System.out.println("=== MAPPER SETUP ===");
        System.out.println("Cache files: " + Arrays.toString(cacheFiles));
        System.out.println("Loaded " + urlMap.size() + " URL mappings");

        if (urlMap.isEmpty()) {
            System.err.println("CRITICAL ERROR: No URL mappings loaded!");
            throw new IOException("Empty URL map");
        }

    }

    @Override
    protected void map(LongWritable key, Text value, Context context)
            throws IOException, InterruptedException {
        // get the filename being processed (e.g. vocab_<safeName>.txt)
        String filename = ((FileSplit)context.getInputSplit())
                              .getPath()
                              .getName();
        // strip prefix and suffix to recover the safeName
        String safeName = filename
            .replaceFirst("^vocab_", "")
            .replaceFirst("\\.txt$", "");

        // look up the real URL
        String url = urlMap.get(safeName);
        if (url == null) {
            // optionally skip or log missing mappings
            System.err.println("MISSING MAPPING FOR: " + safeName);
            return;
        }
        outVal.set(url);

        // tokenize the vocab file’s single line of terms (or multiple lines)
        String line = value.toString();
        StringTokenizer st = new StringTokenizer(line);
        while (st.hasMoreTokens()) {
          String term = st.nextToken();
            outKey.set(term);  // Key = term (e.g., "ecommerce")
            outVal.set(url + "|1");  // Value = "url|1"
            context.write(outKey, outVal);
            context.getCounter("MyMapper", "TOKENS_SEEN").increment(1);

        }
    }
}