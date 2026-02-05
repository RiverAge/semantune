// vite.config.ts
import { defineConfig } from "file:///C:/Users/Mercury/Desktop/src/semantune/frontend/node_modules/vite/dist/node/index.js";
import react from "file:///C:/Users/Mercury/Desktop/src/semantune/frontend/node_modules/@vitejs/plugin-react/dist/index.js";
var __vite_injected_original_dirname = "C:\\Users\\Mercury\\Desktop\\src\\semantune\\frontend";
var vite_config_default = defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": __vite_injected_original_dirname + "/src"
    }
  },
  server: {
    port: 3e3,
    proxy: {
      "/api/v1/tagging/stream": {
        target: "http://localhost:8080",
        changeOrigin: true,
        secure: false,
        ws: false,
        configure: (proxy) => {
          proxy.on("proxyReq", (proxyReq, req) => {
            req.headers["connection"] = "keep-alive";
            req.headers["Cache-Control"] = "no-cache";
          });
          proxy.on("proxyRes", (proxyRes) => {
            delete proxyRes.headers["content-length"];
            proxyRes.headers["cache-control"] = "no-cache, no-transform";
            proxyRes.headers["connection"] = "keep-alive";
          });
          proxy.on("error", (err) => {
            console.log("SSE proxy error", err);
          });
        }
      },
      "/api": {
        target: "http://localhost:8080",
        changeOrigin: true,
        secure: false,
        configure: (proxy, options) => {
          proxy.on("error", (err, req, res) => {
            console.log("proxy error", err);
          });
          proxy.on("proxyReq", (proxyReq, req, res) => {
            console.log("Sending request to the target:", req.method, req.url);
          });
          proxy.on("proxyRes", (proxyRes, req, res) => {
            console.log("Received response from the target:", proxyRes.statusCode, req.url);
          });
        }
      }
    }
  }
});
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJDOlxcXFxVc2Vyc1xcXFxNZXJjdXJ5XFxcXERlc2t0b3BcXFxcc3JjXFxcXHNlbWFudHVuZVxcXFxmcm9udGVuZFwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiQzpcXFxcVXNlcnNcXFxcTWVyY3VyeVxcXFxEZXNrdG9wXFxcXHNyY1xcXFxzZW1hbnR1bmVcXFxcZnJvbnRlbmRcXFxcdml0ZS5jb25maWcudHNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL0M6L1VzZXJzL01lcmN1cnkvRGVza3RvcC9zcmMvc2VtYW50dW5lL2Zyb250ZW5kL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSdcclxuaW1wb3J0IHJlYWN0IGZyb20gJ0B2aXRlanMvcGx1Z2luLXJlYWN0J1xyXG4vLyBpbXBvcnQgcGF0aCBmcm9tICdwYXRoJ1xyXG5cclxuLy8gaHR0cHM6Ly92aXRlanMuZGV2L2NvbmZpZy9cclxuZGVjbGFyZSBjb25zdCBfX2Rpcm5hbWU6IHN0cmluZztcclxuZXhwb3J0IGRlZmF1bHQgZGVmaW5lQ29uZmlnKHtcclxuICBwbHVnaW5zOiBbcmVhY3QoKV0sXHJcbiAgcmVzb2x2ZToge1xyXG4gICAgYWxpYXM6IHtcclxuICAgICAgJ0AnOiBfX2Rpcm5hbWUgKyAnL3NyYycsXHJcbiAgICB9LFxyXG4gIH0sXHJcbiAgc2VydmVyOiB7XG4gICAgcG9ydDogMzAwMCxcbiAgICBwcm94eToge1xuICAgICAgJy9hcGkvdjEvdGFnZ2luZy9zdHJlYW0nOiB7XG4gICAgICAgIHRhcmdldDogJ2h0dHA6Ly9sb2NhbGhvc3Q6ODA4MCcsXG4gICAgICAgIGNoYW5nZU9yaWdpbjogdHJ1ZSxcbiAgICAgICAgc2VjdXJlOiBmYWxzZSxcbiAgICAgICAgd3M6IGZhbHNlLFxuICAgICAgICBjb25maWd1cmU6IChwcm94eSkgPT4ge1xuICAgICAgICAgIHByb3h5Lm9uKCdwcm94eVJlcScsIChwcm94eVJlcSwgcmVxKSA9PiB7XG4gICAgICAgICAgICByZXEuaGVhZGVyc1snY29ubmVjdGlvbiddID0gJ2tlZXAtYWxpdmUnO1xuICAgICAgICAgICAgcmVxLmhlYWRlcnNbJ0NhY2hlLUNvbnRyb2wnXSA9ICduby1jYWNoZSc7XG4gICAgICAgICAgfSk7XG4gICAgICAgICAgcHJveHkub24oJ3Byb3h5UmVzJywgKHByb3h5UmVzKSA9PiB7XG4gICAgICAgICAgICBkZWxldGUgcHJveHlSZXMuaGVhZGVyc1snY29udGVudC1sZW5ndGgnXTtcbiAgICAgICAgICAgIHByb3h5UmVzLmhlYWRlcnNbJ2NhY2hlLWNvbnRyb2wnXSA9ICduby1jYWNoZSwgbm8tdHJhbnNmb3JtJztcbiAgICAgICAgICAgIHByb3h5UmVzLmhlYWRlcnNbJ2Nvbm5lY3Rpb24nXSA9ICdrZWVwLWFsaXZlJztcbiAgICAgICAgICB9KTtcbiAgICAgICAgICBwcm94eS5vbignZXJyb3InLCAoZXJyKSA9PiB7XG4gICAgICAgICAgICBjb25zb2xlLmxvZygnU1NFIHByb3h5IGVycm9yJywgZXJyKTtcbiAgICAgICAgICB9KTtcbiAgICAgICAgfSxcbiAgICAgIH0sXG4gICAgICAnL2FwaSc6IHtcbiAgICAgICAgdGFyZ2V0OiAnaHR0cDovL2xvY2FsaG9zdDo4MDgwJyxcbiAgICAgICAgY2hhbmdlT3JpZ2luOiB0cnVlLFxuICAgICAgICBzZWN1cmU6IGZhbHNlLFxuICAgICAgICBjb25maWd1cmU6IChwcm94eSwgb3B0aW9ucykgPT4ge1xuICAgICAgICAgIHByb3h5Lm9uKCdlcnJvcicsIChlcnIsIHJlcSwgcmVzKSA9PiB7XG4gICAgICAgICAgICBjb25zb2xlLmxvZygncHJveHkgZXJyb3InLCBlcnIpO1xuICAgICAgICAgIH0pO1xuICAgICAgICAgIHByb3h5Lm9uKCdwcm94eVJlcScsIChwcm94eVJlcSwgcmVxLCByZXMpID0+IHtcbiAgICAgICAgICAgIGNvbnNvbGUubG9nKCdTZW5kaW5nIHJlcXVlc3QgdG8gdGhlIHRhcmdldDonLCByZXEubWV0aG9kLCByZXEudXJsKTtcbiAgICAgICAgICB9KTtcbiAgICAgICAgICBwcm94eS5vbigncHJveHlSZXMnLCAocHJveHlSZXMsIHJlcSwgcmVzKSA9PiB7XG4gICAgICAgICAgICBjb25zb2xlLmxvZygnUmVjZWl2ZWQgcmVzcG9uc2UgZnJvbSB0aGUgdGFyZ2V0OicsIHByb3h5UmVzLnN0YXR1c0NvZGUsIHJlcS51cmwpO1xuICAgICAgICAgIH0pO1xuICAgICAgICB9LFxuICAgICAgfSxcbiAgICB9LFxuICB9LFxufSlcclxuIl0sCiAgIm1hcHBpbmdzIjogIjtBQUE2VSxTQUFTLG9CQUFvQjtBQUMxVyxPQUFPLFdBQVc7QUFEbEIsSUFBTSxtQ0FBbUM7QUFNekMsSUFBTyxzQkFBUSxhQUFhO0FBQUEsRUFDMUIsU0FBUyxDQUFDLE1BQU0sQ0FBQztBQUFBLEVBQ2pCLFNBQVM7QUFBQSxJQUNQLE9BQU87QUFBQSxNQUNMLEtBQUssbUNBQVk7QUFBQSxJQUNuQjtBQUFBLEVBQ0Y7QUFBQSxFQUNBLFFBQVE7QUFBQSxJQUNOLE1BQU07QUFBQSxJQUNOLE9BQU87QUFBQSxNQUNMLDBCQUEwQjtBQUFBLFFBQ3hCLFFBQVE7QUFBQSxRQUNSLGNBQWM7QUFBQSxRQUNkLFFBQVE7QUFBQSxRQUNSLElBQUk7QUFBQSxRQUNKLFdBQVcsQ0FBQyxVQUFVO0FBQ3BCLGdCQUFNLEdBQUcsWUFBWSxDQUFDLFVBQVUsUUFBUTtBQUN0QyxnQkFBSSxRQUFRLFlBQVksSUFBSTtBQUM1QixnQkFBSSxRQUFRLGVBQWUsSUFBSTtBQUFBLFVBQ2pDLENBQUM7QUFDRCxnQkFBTSxHQUFHLFlBQVksQ0FBQyxhQUFhO0FBQ2pDLG1CQUFPLFNBQVMsUUFBUSxnQkFBZ0I7QUFDeEMscUJBQVMsUUFBUSxlQUFlLElBQUk7QUFDcEMscUJBQVMsUUFBUSxZQUFZLElBQUk7QUFBQSxVQUNuQyxDQUFDO0FBQ0QsZ0JBQU0sR0FBRyxTQUFTLENBQUMsUUFBUTtBQUN6QixvQkFBUSxJQUFJLG1CQUFtQixHQUFHO0FBQUEsVUFDcEMsQ0FBQztBQUFBLFFBQ0g7QUFBQSxNQUNGO0FBQUEsTUFDQSxRQUFRO0FBQUEsUUFDTixRQUFRO0FBQUEsUUFDUixjQUFjO0FBQUEsUUFDZCxRQUFRO0FBQUEsUUFDUixXQUFXLENBQUMsT0FBTyxZQUFZO0FBQzdCLGdCQUFNLEdBQUcsU0FBUyxDQUFDLEtBQUssS0FBSyxRQUFRO0FBQ25DLG9CQUFRLElBQUksZUFBZSxHQUFHO0FBQUEsVUFDaEMsQ0FBQztBQUNELGdCQUFNLEdBQUcsWUFBWSxDQUFDLFVBQVUsS0FBSyxRQUFRO0FBQzNDLG9CQUFRLElBQUksa0NBQWtDLElBQUksUUFBUSxJQUFJLEdBQUc7QUFBQSxVQUNuRSxDQUFDO0FBQ0QsZ0JBQU0sR0FBRyxZQUFZLENBQUMsVUFBVSxLQUFLLFFBQVE7QUFDM0Msb0JBQVEsSUFBSSxzQ0FBc0MsU0FBUyxZQUFZLElBQUksR0FBRztBQUFBLFVBQ2hGLENBQUM7QUFBQSxRQUNIO0FBQUEsTUFDRjtBQUFBLElBQ0Y7QUFBQSxFQUNGO0FBQ0YsQ0FBQzsiLAogICJuYW1lcyI6IFtdCn0K
