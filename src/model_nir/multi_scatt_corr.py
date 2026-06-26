## multiplicative_scatter_correction.py

class msc(TransformerMixin, BaseEstimator):
    
    def __init__(self, reference=None):
        self.reference = reference
 
    def fit(self, X, y=None):  
        
        X = self._validate_data(X, accept_sparse=True)
        
        # Mean centre correction
        X -=  X.mean(axis=1)[:,np.newaxis]
        
        # If the reference doesn't exist, set it to the average spectrum
        if self.reference is None:
            self.reference =  X.mean(axis=0)
        
        self.is_fitted_ = True
        
        # Fit function must always return self
        return self    
    
    def transform(self, X, y=None):
        check_is_fitted(self)
        
        # Input validation
        X = check_array(X)
        
        # Mean centre correction
        X -=  X.mean(axis=1)[:,np.newaxis]
 
        # MSC Correction
        Xmsc = np.zeros_like(X)
        for i in range(X.shape[0]):
            # Run regression
            fit = np.polyfit(self.reference, X[i,:], 1, full=True)
            # Apply correction
            Xmsc[i,:] = (X[i,:] - fit[0][1]) / fit[0][0]
        
        return Xmsc 
    

##################

def msc(input_data, reference=None):
    ''' Perform Multiplicative scatter correction'''
 
    # mean centre correction
    for i in range(input_data.shape[0]):
        input_data[i,:] -= input_data[i,:].mean()
 
    # Get the reference spectrum. If not given, estimate it from the mean    
    if reference is None:    
        # Calculate mean
        ref = np.mean(input_data, axis=0)
    else:
        ref = reference
 
    # Define a new array and populate it with the corrected data    
    data_msc = np.zeros_like(input_data)
    for i in range(input_data.shape[0]):
        # Run regression
        fit = np.polyfit(ref, input_data[i,:], 1, full=True)
        # Apply correction
        data_msc[i,:] = (input_data[i,:] - fit[0][1]) / fit[0][0] 
 
    return (data_msc, ref)