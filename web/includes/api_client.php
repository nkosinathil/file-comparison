<?php
/**
 * API Client for Aurex Backend
 */

class APIClient {
    private $baseUrl;
    private $token;
    private $timeout;
    
    public function __construct($baseUrl = null, $token = null) {
        $this->baseUrl = $baseUrl ?: API_BASE_URL;
        $this->token = $token;
        $this->timeout = API_TIMEOUT;
    }
    
    public function setToken($token) {
        $this->token = $token;
    }
    
    /**
     * Make HTTP request to API
     */
    private function request($method, $endpoint, $data = null, $files = null) {
        $url = $this->baseUrl . $endpoint;
        
        $ch = curl_init();
        
        $headers = [
            'Accept: application/json',
        ];
        
        if ($this->token) {
            $headers[] = 'Authorization: Bearer ' . $this->token;
        }
        
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, $this->timeout);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        
        if ($method === 'POST' || $method === 'PUT') {
            if ($files) {
                // Multipart form data for file uploads
                $postData = $data ?: [];
                foreach ($files as $key => $file) {
                    $postData[$key] = new CURLFile($file['tmp_name'], $file['type'], $file['name']);
                }
                curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
            } else if ($data) {
                $headers[] = 'Content-Type: application/json';
                curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
            }
        }
        
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        
        curl_close($ch);
        
        if ($error) {
            throw new Exception("API Request Error: " . $error);
        }
        
        $result = json_decode($response, true);
        
        if ($httpCode >= 400) {
            $errorMsg = isset($result['detail']) ? $result['detail'] : 'Unknown error';
            throw new Exception("API Error ($httpCode): " . $errorMsg);
        }
        
        return $result;
    }
    
    /**
     * Authentication
     */
    public function login($username, $password) {
        $data = http_build_query([
            'username' => $username,
            'password' => $password,
            'grant_type' => 'password'
        ]);
        
        $ch = curl_init($this->baseUrl . '/api/auth/token');
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/x-www-form-urlencoded'
        ]);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        if ($httpCode !== 200) {
            throw new Exception("Login failed: Invalid credentials");
        }
        
        return json_decode($response, true);
    }
    
    public function getCurrentUser() {
        return $this->request('GET', '/api/auth/me');
    }
    
    /**
     * OAuth SSO
     */
    public function initiateOAuth($clientId, $redirectUri) {
        return $this->request('GET', '/api/sso/oauth/authorize', [
            'client_id' => $clientId,
            'redirect_uri' => $redirectUri,
            'response_type' => 'code',
            'scope' => 'openid profile email'
        ]);
    }
    
    public function handleOAuthCallback($code, $state) {
        return $this->request('POST', '/api/sso/oauth/callback', [
            'code' => $code,
            'state' => $state
        ]);
    }
    
    /**
     * SAML SSO
     */
    public function handleSAMLLogin($samlResponse) {
        return $this->request('POST', '/api/sso/saml/login', [
            'saml_response' => $samlResponse
        ]);
    }
    
    /**
     * Cases
     */
    public function getCases($finishedOnly = false) {
        $endpoint = '/api/cases';
        if ($finishedOnly) {
            $endpoint .= '?finished_only=true';
        }
        return $this->request('GET', $endpoint);
    }
    
    public function getCase($caseId) {
        return $this->request('GET', "/api/cases/{$caseId}");
    }
    
    public function createCase($data) {
        return $this->request('POST', '/api/cases', $data);
    }
    
    public function deleteCase($caseId) {
        return $this->request('DELETE', "/api/cases/{$caseId}");
    }
    
    /**
     * Processing
     */
    public function startProcessing($caseId) {
        return $this->request('POST', "/api/cases/{$caseId}/process");
    }
    
    public function cancelProcessing($caseId) {
        return $this->request('POST', "/api/cases/{$caseId}/cancel");
    }
    
    public function getProcessingStatus($caseId) {
        return $this->request('GET', "/api/cases/{$caseId}/status");
    }
    
    /**
     * File Upload
     */
    public function uploadFiles($caseId, $files) {
        return $this->request('POST', "/api/cases/{$caseId}/upload", null, $files);
    }
    
    /**
     * Analysis
     */
    public function chatQuery($caseId, $message, $history = []) {
        return $this->request('POST', '/api/analysis/chat', [
            'case_id' => $caseId,
            'message' => $message,
            'conversation_history' => $history
        ]);
    }
    
    public function getInsights($caseId) {
        return $this->request('POST', '/api/analysis/insights', [
            'case_id' => $caseId
        ]);
    }
    
    /**
     * System
     */
    public function healthCheck() {
        return $this->request('GET', '/api/health');
    }
    
    public function getVersion() {
        return $this->request('GET', '/api/version');
    }
}
